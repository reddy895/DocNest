import logging
from typing import Optional, List, Dict, Any
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("docnest.ollama")


class OllamaService:
    """
    Robust asynchronous connector for the local Ollama LLM runtime.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL
        self.timeout = float(settings.OLLAMA_TIMEOUT)

    async def check_health(self) -> Dict[str, Any]:
        """
        Verify connection to Ollama and determine available models.
        """
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    has_model = any(self.default_model in m for m in models)
                    return {
                        "connected": True,
                        "models": models,
                        "has_target_model": has_model,
                        "target_model": self.default_model,
                    }
        except Exception as exc:
            logger.warning(f"Ollama connection check failed: {exc}")
            return {
                "connected": False,
                "error": str(exc),
                "models": [],
                "has_target_model": False,
                "target_model": self.default_model,
            }
        return {"connected": False, "models": [], "has_target_model": False}

    async def get_active_model(self) -> str:
        """
        Determine the best active model to query, falling back to any available llama model.
        """
        health = await self.check_health()
        if not health.get("connected"):
            return self.default_model

        models: List[str] = health.get("models", [])
        # Prefer exact or close matches
        for m in models:
            if self.default_model in m:
                return m
        for m in models:
            if "llama" in m.lower():
                return m
        # Ignore embedding models
        for m in models:
            if "embed" not in m.lower():
                return m

        return models[0] if models else self.default_model

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Generate completion using Ollama HTTP API with timeout protection and structured error handling.
        """
        target_model = model or await self.get_active_model()
        url = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            logger.info(f"Dispatching query to Ollama model '{target_model}'...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("response", "").strip()
                    return answer
                elif resp.status_code == 404:
                    return (
                        f"Ollama error: Model '{target_model}' not found. "
                        f"Run `ollama pull {target_model}` to download it."
                    )
                else:
                    return f"Ollama generation failed (HTTP {resp.status_code}): {resp.text}"

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}.")
            return (
                "Cannot connect to the local Ollama service. "
                "Please verify that Ollama is running (`ollama serve`)."
            )
        except httpx.TimeoutException:
            logger.error(f"Ollama generation timed out after {self.timeout}s.")
            return "Response generation timed out. Please try a simpler query or check system load."
        except Exception as exc:
            logger.error(f"Unexpected Ollama client error: {exc}", exc_info=True)
            return f"An error occurred while generating the answer: {str(exc)}"


# Global Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
