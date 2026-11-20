import time
import logging
from typing import Optional, List, Dict, Any
import httpx

from backend.app.core.config import settings

logger = logging.getLogger("docnest.models")


class ModelConfigService:
    """
    Manages discovery of local Ollama models, remote LLM configurations,
    and hyperparameter profiles (temperature, context windows, top_k).
    """

    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._cached_models: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl_seconds: float = 30.0  # 30-second TTL

    async def list_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover locally pulled Ollama models and cloud fallback definitions.
        """
        now = time.time()
        if not force_refresh and self._cached_models and (now - self._cache_timestamp < self._cache_ttl_seconds):
            return self._cached_models

        discovered: List[Dict[str, Any]] = []

        # 1. Query Ollama /api/tags
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.ollama_base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = data.get("models", [])
                    for m in models:
                        name = m.get("name", "")
                        size_gb = round(m.get("size", 0) / (1024 ** 3), 2)
                        family = m.get("details", {}).get("family", "llama")
                        param_size = m.get("details", {}).get("parameter_size", "unknown")
                        discovered.append({
                            "id": name,
                            "name": name,
                            "provider": "ollama_local",
                            "size_gb": size_gb,
                            "parameter_size": param_size,
                            "family": family,
                            "is_active": name == settings.OLLAMA_MODEL,
                            "is_local": True,
                        })
        except Exception as exc:
            logger.debug(f"Ollama dynamic tags discovery error (using fallback definitions): {exc}")

        # 2. Add standard curated presets if not detected
        defaults = [
            {"id": "llama3.2", "name": "Llama 3.2 (3B)", "provider": "ollama_local", "family": "llama", "parameter_size": "3B", "size_gb": 2.0, "is_local": True},
            {"id": "llama3.1:8b", "name": "Llama 3.1 (8B)", "provider": "ollama_local", "family": "llama", "parameter_size": "8B", "size_gb": 4.7, "is_local": True},
            {"id": "mistral:7b", "name": "Mistral (7B)", "provider": "ollama_local", "family": "mistral", "parameter_size": "7B", "size_gb": 4.1, "is_local": True},
            {"id": "qwen2.5:7b", "name": "Qwen 2.5 (7B)", "provider": "ollama_local", "family": "qwen", "parameter_size": "7B", "size_gb": 4.4, "is_local": True},
            {"id": "deepseek-r1:8b", "name": "DeepSeek R1 (8B)", "provider": "ollama_local", "family": "deepseek", "parameter_size": "8B", "size_gb": 4.9, "is_local": True},
        ]

        existing_ids = {m["id"] for m in discovered}
        for d in defaults:
            if d["id"] not in existing_ids:
                d["is_active"] = d["id"] == settings.OLLAMA_MODEL
                discovered.append(d)

        self._cached_models = discovered
        self._cache_timestamp = now
        return discovered

    async def test_model_connection(self, model_name: str) -> Dict[str, Any]:
        """Verify model connectivity, latency, and operational health."""
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "Respond with 'ready' if online.",
                        "stream": False,
                    },
                )
                latency_ms = round((time.time() - start) * 1000, 2)
                if res.status_code == 200:
                    return {
                        "status": "online",
                        "model": model_name,
                        "latency_ms": latency_ms,
                        "error": None,
                    }
                else:
                    return {
                        "status": "error",
                        "model": model_name,
                        "latency_ms": latency_ms,
                        "error": f"HTTP {res.status_code}: {res.text[:100]}",
                    }
        except Exception as e:
            return {
                "status": "offline",
                "model": model_name,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "error": str(e),
            }


_model_service: Optional[ModelConfigService] = None


def get_model_config_service() -> ModelConfigService:
    global _model_service
    if _model_service is None:
        _model_service = ModelConfigService()
    return _model_service
