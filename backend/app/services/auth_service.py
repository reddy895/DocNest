import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import bcrypt
import jwt

from backend.app.core.config import settings
from backend.app.core.database import get_db_connection
from backend.app.core.mongo import get_mongo_db
from backend.app.models.auth import UserOut

logger = logging.getLogger("docnest.auth")


class AuthService:
    """
    Core authentication service managing password hashing, JWT generation,
    refresh tokens, and user credentials across MongoDB and SQLite.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash plaintext password using bcrypt with 12 salt rounds."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Securely verify plaintext password against stored bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create signed JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        })
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create 7-day signed JWT refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT access or refresh token."""
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except (jwt.PyJWTError, Exception) as exc:
            logger.debug(f"Token decode failure: {exc}")
            return None

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        workspace_name: Optional[str] = None,
    ) -> Tuple[UserOut, str, str]:
        """
        Register a new user, initializing workspace, settings, and returning tokens.
        """
        normalized_email = email.lower().strip()
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        pwd_hash = self.hash_password(password)
        ws_name = workspace_name.strip() if workspace_name else f"{username}'s Workspace"

        # Check existing user
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT id FROM users WHERE email = ?", (normalized_email,))
            if await cursor.fetchone():
                raise ValueError("A user with this email address already exists.")

            await db.execute(
                """
                INSERT INTO users (id, email, username, password_hash, workspace_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, normalized_email, username.strip(), pwd_hash, ws_name, now_iso),
            )

            # Initialize default user RAG settings
            await db.execute(
                """
                INSERT INTO user_settings (
                    user_id, chunk_size, chunk_overlap, top_k,
                    min_relevance_score, temperature, hybrid_enabled,
                    reranker_enabled, preset_name, updated_at
                )
                VALUES (?, 512, 64, 5, 0.30, 0.1, 1, 1, 'balanced', ?)
                """,
                (user_id, now_iso),
            )
            await db.commit()

        # Dual write to MongoDB if available
        mongo_db = get_mongo_db()
        if mongo_db:
            try:
                await mongo_db.users.insert_one({
                    "id": user_id,
                    "email": normalized_email,
                    "username": username.strip(),
                    "password_hash": pwd_hash,
                    "workspace_name": ws_name,
                    "created_at": now_iso,
                })
            except Exception as m_err:
                logger.debug(f"MongoDB user sync deferred: {m_err}")

        user_out = UserOut(
            id=user_id,
            email=normalized_email,
            username=username.strip(),
            workspace_name=ws_name,
            created_at=now_iso,
        )
        access_token = self.create_access_token({"sub": user_id, "email": normalized_email})
        refresh_token = self.create_refresh_token(user_id)

        return user_out, access_token, refresh_token

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[UserOut, str, str]:
        """
        Authenticate user credentials and return UserOut and refreshed tokens.
        """
        normalized_email = email.lower().strip()
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT id, email, username, password_hash, workspace_name, created_at FROM users WHERE email = ?",
                (normalized_email,),
            )
            row = await cursor.fetchone()

            if not row or not self.verify_password(password, row["password_hash"]):
                raise ValueError("Incorrect email or password.")

            user_out = UserOut(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                workspace_name=row["workspace_name"],
                created_at=row["created_at"],
            )

        access_token = self.create_access_token({"sub": user_out.id, "email": user_out.email})
        refresh_token = self.create_refresh_token(user_out.id)
        return user_out, access_token, refresh_token

    async def get_user_by_id(self, user_id: str) -> Optional[UserOut]:
        """Fetch user profile by user_id."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT id, email, username, workspace_name, created_at FROM users WHERE id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return UserOut(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                workspace_name=row["workspace_name"],
                created_at=row["created_at"],
            )


_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Singleton provider for AuthService."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
