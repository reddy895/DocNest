"""Isolated Ollama provider adapter implementing the unified LLMProvider interface."""

import json
from typing import AsyncGenerator, List, Optional
import httpx
from backend.app.core.config import settings
from backend.intelligence.model_compatibility.registry import LLMProvider, ProviderHealth


class OllamaProviderAdapter(LLMProvider):
    """Adapter for local Ollama runtime supporting discovery, health, and streaming."""

    provider_name = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OLLAMA_MODEL
        self.timeout = timeout

    async def check_health(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    models = [m.get("name", "") for m in resp.json().get("models", []) if m.get("name")]
                    return ProviderHealth(provider=self.provider_name, available=True, installed_models=models)
                return ProviderHealth(
                    provider=self.provider_name,
                    available=False,
                    error=f"HTTP {resp.status_code}",
                )
        except Exception as exc:
            return ProviderHealth(provider=self.provider_name, available=False, error=str(exc))

    async def list_models(self) -> List[str]:
        health = await self.check_health()
        return [m for m in health.installed_models if "embed" not in m.lower()]

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break

