import time
import httpx
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.core.telemetry import telemetry

router = APIRouter(prefix="/api/system", tags=["System"])

START_TIME = time.time()


@router.get("/health")
async def get_system_health():
    """
    Live health check reporting Ollama runtime, ChromaDB vectors, and system status.
    """
    uptime_seconds = time.time() - START_TIME
    ollama_status = "unavailable"
    ollama_models = []
    has_target_model = False
    ping_ms = 0.0

    try:
        t0 = time.time()
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ping_ms = round((time.time() - t0) * 1000, 1)
            if resp.status_code == 200:
                ollama_status = "connected"
                data = resp.json()
                models = data.get("models", [])
                ollama_models = [m.get("name", "") for m in models]
                has_target_model = any(settings.OLLAMA_MODEL in m for m in ollama_models)
    except Exception as exc:
        ollama_status = f"disconnected: {str(exc)}"

    chroma_dir_exists = settings.CHROMA_DIR.exists()
    docs_dir_exists = settings.DOCUMENTS_DIR.exists()

    overall_status = "healthy" if ollama_status == "connected" else "degraded"

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
                "ping_ms": ping_ms,
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
                "db_path": str(settings.DB_PATH),
            },
            "rag": {
                "embedding_model": settings.EMBEDDING_MODEL,
                "reranker_model": settings.RERANKER_MODEL,
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "top_k": settings.RETRIEVAL_TOP_K,
                "min_relevance_score": settings.MIN_RELEVANCE_SCORE,
                "hybrid_enabled": settings.HYBRID_SEARCH_ENABLED,
                "reranker_enabled": settings.RERANKER_ENABLED,
            },
        },
    }


@router.get("/telemetry")
async def get_system_telemetry():
    """
    Get aggregate RAG operational telemetry including retrieval latency and feedback.
    """
    return telemetry.get_summary()
