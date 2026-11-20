import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.core.config import settings
from backend.app.services.model_config_service import get_model_config_service

logger = logging.getLogger("docnest.api.models")
router = APIRouter(prefix="/api/models", tags=["Models"])


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    family: Optional[str] = "llama"
    parameter_size: Optional[str] = "unknown"
    size_gb: Optional[float] = 0.0
    is_active: bool = False
    is_local: bool = True


class TestModelRequest(BaseModel):
    model: str = Field(min_length=1)


class TestModelResponse(BaseModel):
    status: str
    model: str
    latency_ms: float
    error: Optional[str] = None


class SwitchModelRequest(BaseModel):
    model: str = Field(min_length=1)


class SwitchModelResponse(BaseModel):
    success: bool
    active_model: str
    message: str


@router.get("", response_model=List[ModelInfo])
async def list_models(
    refresh: bool = Query(False, description="Force refresh local model detection"),
):
    """List all locally installed Ollama models and available presets."""
    svc = get_model_config_service()
    models = await svc.list_available_models(force_refresh=refresh)
    # Mark active model
    return [
        ModelInfo(
            **{**m, "is_active": m["id"] == settings.OLLAMA_MODEL or m["name"] == settings.OLLAMA_MODEL}
        )
        for m in models
    ]


@router.post("/test", response_model=TestModelResponse)
async def test_model(payload: TestModelRequest):
    """Probe model connectivity and benchmark response latency."""
    svc = get_model_config_service()
    res = await svc.test_model_connection(payload.model)
    return TestModelResponse(**res)


@router.post("/switch", response_model=SwitchModelResponse)
async def switch_model(payload: SwitchModelRequest):
    """Switch active generative LLM model in system runtime."""
    settings.OLLAMA_MODEL = payload.model
    logger.info(f"Active generative model switched to: {payload.model}")
    return SwitchModelResponse(
        success=True,
        active_model=payload.model,
        message=f"Active model successfully switched to {payload.model}",
    )
