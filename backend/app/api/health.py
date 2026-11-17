import time
import httpx
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(prefix="/api/health", tags=["Health"])

START_TIME = time.time()


@router.get("")
async def get_health():
    """
    Comprehensive system health check reporting backend, Ollama, and vector store status.
    """
    uptime_seconds = time.time() - START_TIME

    # Check Ollama status
    ollama_status = "unavailable"
    ollama_models = []
    has_target_model = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_status = "connected"
                data = resp.json()
                models = data.get("models", [])
                ollama_models = [m.get("name", "") for m in models]
                has_target_model = any(settings.OLLAMA_MODEL in m for m in ollama_models)
    except Exception as exc:
        ollama_status = f"disconnected: {str(exc)}"

    # Check Chroma storage directory
    chroma_dir_exists = settings.CHROMA_DIR.exists()
    docs_dir_exists = settings.DOCUMENTS_DIR.exists()

    overall_status = "healthy"
    if ollama_status != "connected":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "app_name": "DocNest",
        "version": "1.0.0",
        "uptime_seconds": round(uptime_seconds, 2),
        "environment": settings.ENV,
        "components": {
            "api": {"status": "operational"},
            "ollama": {
                "status": ollama_status,
                "base_url": settings.OLLAMA_BASE_URL,
                "configured_model": settings.OLLAMA_MODEL,
                "model_available": has_target_model,
                "available_models": ollama_models,
            },
            "storage": {
                "documents_dir": str(settings.DOCUMENTS_DIR),
                "documents_dir_ready": docs_dir_exists,
                "chroma_dir": str(settings.CHROMA_DIR),
                "chroma_dir_ready": chroma_dir_exists,
            },
            "rag": {
                "embedding_model": settings.EMBEDDING_MODEL,
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "top_k": settings.RETRIEVAL_TOP_K,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            },
        },
    }
