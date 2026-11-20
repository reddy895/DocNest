from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from backend.app.core.config import settings


def hash_password(password: str) -> str:
    """Hash plain password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except (jwt.PyJWTError, Exception):
        return None


def validate_file_size_and_extension(filename: str, file_size_bytes: int) -> tuple[bool, Optional[str]]:
    """
    Validate that an incoming document upload conforms to allowed extensions and size bounds.
    """
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
        return False, f"Unsupported file extension '{ext}'. Allowed extensions: {allowed}"

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File size exceeds maximum permitted limit of {settings.MAX_FILE_SIZE_MB}MB."

    if file_size_bytes == 0:
        return False, "File is completely empty (0 bytes)."

    return True, None

