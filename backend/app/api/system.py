import time
import httpx
import logging
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.core.telemetry import telemetry
from backend.app.services.chroma_service import get_chroma_service
from backend.app.services.bm25_service import get_bm25_service

logger = logging.getLogger("docnest.api.system")
router = APIRouter(prefix="/api/system", tags=["System"])

START_TIME = time.time()


@router.get("/health")
async def get_system_health():
    """
    Live health check reporting Ollama runtime, ChromaDB vectors,
    BM25 sparse index, and Cross-Encoder reranker latencies.
    """
    uptime_seconds = time.time() - START_TIME

    # 1. Ollama Health & Latency
    ollama_status = "unavailable"
    ollama_models = []
    has_target_model = False
    ollama_latency_ms = 0.0

    try:
        t0 = time.time()
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ollama_latency_ms = round((time.time() - t0) * 1000, 1)
            if resp.status_code == 200:
                ollama_status = "connected"
                data = resp.json()
                models = data.get("models", [])
                ollama_models = [m.get("name", "") for m in models]
                has_target_model = any(settings.OLLAMA_MODEL in m for m in ollama_models)
    except Exception as exc:
        ollama_status = f"disconnected: {str(exc)}"

    # 2. ChromaDB Health & Chunk Count
    chroma_status = "operational"
    chroma_latency_ms = 0.0
    total_vectors = 0
    try:
        t1 = time.time()
        chroma = get_chroma_service()
        total_vectors = chroma.count()
        chroma_latency_ms = round((time.time() - t1) * 1000, 1)
    except Exception as exc:
        chroma_status = f"degraded: {exc}"

    # 3. BM25 Sparse Index Health
    bm25_status = "operational"
    bm25_count = 0
    try:
        bm25 = get_bm25_service()
        bm25_count = len(bm25.corpus)
    except Exception as exc:
        bm25_status = f"degraded: {exc}"

    # 4. Cross-Encoder Reranker Health
    reranker_status = "ready"
    reranker_latency_ms = 0.0
    try:
        t2 = time.time()
        from backend.app.services.reranker_service import get_reranker
        # Ensure reranker is referenced
        r = get_reranker()
        reranker_latency_ms = round((time.time() - t2) * 1000, 1)
    except Exception as exc:
        reranker_status = f"unavailable: {exc}"

    # Overall Status Calculation
    if ollama_status == "connected" and chroma_status == "operational":
        overall_status = "healthy"
    elif chroma_status == "operational":
        overall_status = "degraded"
    else:
        overall_status = "offline"

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
                "latency_ms": ollama_latency_ms,
                "base_url": settings.OLLAMA_BASE_URL,
                "configured_model": settings.OLLAMA_MODEL,
                "model_available": has_target_model,
                "available_models": ollama_models,
            },
            "chroma": {
                "status": chroma_status,
                "latency_ms": chroma_latency_ms,
                "total_chunks": total_vectors,
                "collection": settings.COLLECTION_NAME,
            },
            "bm25": {
                "status": bm25_status,
                "indexed_chunks": bm25_count,
            },
            "reranker": {
                "status": reranker_status,
                "model": settings.RERANKER_MODEL,
                "latency_ms": reranker_latency_ms,
            },
            "rag": {
                "embedding_model": settings.EMBEDDING_MODEL,
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
