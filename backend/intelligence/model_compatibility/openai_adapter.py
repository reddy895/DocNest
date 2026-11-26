"""OpenAI-compatible provider adapter with streaming and health verification."""

import json
import os
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from backend.intelligence.model_compatibility.registry import LLMProvider, ProviderHealth


class OpenAICompatibleAdapter(LLMProvider):
    """Supports OpenAI, vLLM, LM Studio, and compatible /v1 endpoints."""

    provider_name = "openai_compatible"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or os.getenv("DOCNEST_OPENAI_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("DOCNEST_OPENAI_API_KEY", "")
        self.default_model = default_model
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def check_health(self) -> ProviderHealth:
        if not self.is_configured():
            return ProviderHealth(
                provider=self.provider_name,
                available=False,
                error="Base URL not configured",
            )
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    models = [m.get("id", "") for m in data if m.get("id")]
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
        return health.installed_models

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("OpenAI-compatible provider base_url is not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, object] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            choices = resp.json().get("choices", [])
            return choices[0]["message"]["content"].strip() if choices else ""

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        if not self.is_configured():
            raise RuntimeError("OpenAI-compatible provider base_url is not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    chunk_json = json.loads(data_str)
                    delta = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        yield delta

