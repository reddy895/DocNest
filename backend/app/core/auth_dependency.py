from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import aiosqlite
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.auth import UserOut

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: aiosqlite.Connection = Depends(get_db),
) -> UserOut:
    """
    Extract and validate current authenticated user from Bearer JWT token.
    Falls back to a default local admin user if running without credentials in local mode.
    """
    if credentials:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_id = payload["sub"]
            cursor = await db.execute(
                "SELECT id, email, username, workspace_name, created_at FROM users WHERE id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            if row:
                return UserOut(
                    id=row["id"],
                    email=row["email"],
                    username=row["username"],
                    workspace_name=row["workspace_name"],
                    created_at=row["created_at"],
                )

    # In local single-user mode, fallback to default local operator
    cursor = await db.execute("SELECT id, email, username, workspace_name, created_at FROM users LIMIT 1")
    row = await cursor.fetchone()
    if row:
        return UserOut(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            workspace_name=row["workspace_name"],
            created_at=row["created_at"],
        )

    # If database has no users at all, provision default local user
    default_id = "user_default_local"
    await db.execute(
        """
        INSERT OR IGNORE INTO users (id, email, username, password_hash, workspace_name, created_at)
        VALUES (?, 'local@docnest.ai', 'Local Operator', '', 'Default Workspace', datetime('now'))
        """,
        (default_id,),
    )
    await db.commit()
    return UserOut(
        id=default_id,
        email="local@docnest.ai",
        username="Local Operator",
        workspace_name="Default Workspace",
        created_at="2026-01-01T00:00:00Z",
    )


async def get_required_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: aiosqlite.Connection = Depends(get_db),
) -> UserOut:
    """Strict authentication dependency rejecting unauthenticated requests."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload["sub"]
    cursor = await db.execute(
        "SELECT id, email, username, workspace_name, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found.",
        )
    return UserOut(
        id=row["id"],
        email=row["email"],
        username=row["username"],
        workspace_name=row["workspace_name"],
        created_at=row["created_at"],
    )
