import logging
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import (
    UserRegister,
    UserLogin,
    UserOut,
    Token,
    RefreshTokenRequest,
)
from backend.app.services.auth_service import get_auth_service

logger = logging.getLogger("docnest.api.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    """Register a new user account with an isolated workspace and default settings."""
    auth_service = get_auth_service()
    try:
        user_out, access_token, refresh_token = await auth_service.register_user(
            email=user_in.email,
            username=user_in.username,
            password=user_in.password,
            workspace_name=user_in.workspace_name,
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_out,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as exc:
        logger.error(f"Registration failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration could not be completed at this time.",
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Authenticate with email and password to receive JWT access and refresh tokens."""
    auth_service = get_auth_service()
    try:
        user_out, access_token, refresh_token = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password,
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_out,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error(f"Login failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to internal error.",
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(payload: RefreshTokenRequest):
    """Exchange a valid refresh token for a fresh access token."""
    auth_service = get_auth_service()
    decoded = auth_service.decode_token(payload.refresh_token)

    if not decoded or decoded.get("type") != "refresh" or not decoded.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decoded["sub"]
    user_out = await auth_service.get_user_by_id(user_id)
    if not user_out:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with refresh token no longer exists.",
        )

    new_access_token = auth_service.create_access_token({
        "sub": user_out.id,
        "email": user_out.email,
    })
    new_refresh_token = auth_service.create_refresh_token(user_out.id)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=user_out,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    """Get profile of current authenticated user."""
    return current_user
