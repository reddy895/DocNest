import uuid
from datetime import datetime, timezone
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import UserRegister, UserLogin, UserOut, Token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: aiosqlite.Connection = Depends(get_db)):
    """Register a new user account with an isolated workspace."""
    # Check if email exists
    cursor = await db.execute("SELECT id FROM users WHERE email = ?", (user_in.email.lower(),))
    if await cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    pwd_hash = hash_password(user_in.password)
    workspace = user_in.workspace_name or f"{user_in.username}'s Workspace"

    await db.execute(
        """
        INSERT INTO users (id, email, username, password_hash, workspace_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, user_in.email.lower(), user_in.username, pwd_hash, workspace, now_iso),
    )

    # Initialize default user RAG settings
    await db.execute(
        """
        INSERT INTO user_settings (user_id, chunk_size, chunk_overlap, top_k, min_relevance_score, temperature, hybrid_enabled, reranker_enabled, preset_name, updated_at)
        VALUES (?, 512, 64, 5, 0.30, 0.1, 1, 1, 'balanced', ?)
        """,
        (user_id, now_iso),
    )
    await db.commit()

    user_out = UserOut(
        id=user_id,
        email=user_in.email.lower(),
        username=user_in.username,
        workspace_name=workspace,
        created_at=now_iso,
    )
    token = create_access_token({"sub": user_id, "email": user_out.email})

    return Token(access_token=token, user=user_out)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    """Authenticate with email and password to receive JWT access token."""
    cursor = await db.execute(
        "SELECT id, email, username, password_hash, workspace_name, created_at FROM users WHERE email = ?",
        (credentials.email.lower(),),
    )
    row = await cursor.fetchone()
    if not row or not verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    user_out = UserOut(
        id=row["id"],
        email=row["email"],
        username=row["username"],
        workspace_name=row["workspace_name"],
        created_at=row["created_at"],
    )
    token = create_access_token({"sub": row["id"], "email": row["email"]})
    return Token(access_token=token, user=user_out)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    """Get profile of current authenticated user."""
    return current_user
