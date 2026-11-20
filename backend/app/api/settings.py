import logging
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import UserOut
from backend.app.models.settings import UserSettingsModel, PresetApplyRequest, RAG_PRESETS
from backend.app.services.settings_service import get_settings_service

logger = logging.getLogger("docnest.api.settings")
router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=UserSettingsModel)
async def get_user_settings(current_user: UserOut = Depends(get_current_user)):
    """Retrieve persisted RAG pipeline configuration for current user."""
    svc = get_settings_service()
    return await svc.get_user_settings(current_user.id)


@router.put("", response_model=UserSettingsModel)
async def update_user_settings(
    settings_in: UserSettingsModel,
    current_user: UserOut = Depends(get_current_user),
):
    """Update custom RAG pipeline parameters."""
    svc = get_settings_service()
    return await svc.update_user_settings(current_user.id, settings_in)


@router.post("/preset", response_model=UserSettingsModel)
async def apply_preset(
    req: PresetApplyRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """Apply a 1-click RAG pipeline preset (strict, balanced, or deep)."""
    svc = get_settings_service()
    try:
        return await svc.apply_preset(current_user.id, req.preset_name)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/presets")
async def list_presets():
    """List all available pipeline presets and their hyperparameter definitions."""
    return RAG_PRESETS
