"""Unified LLMProvider interface and model family capability registry."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelCapabilities(BaseModel):
    model_id: str
    family: str
    provider: str
    context_window: int = 8192
    supports_streaming: bool = True
    supports_structured_output: bool = True
    supports_tools: bool = False
    is_embedding_model: bool = False
    recommended_ram_gb: int = 8
    notes: str = ""


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    installed_models: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class LLMProvider(ABC):
    """Abstract interface for isolated model providers (Ollama, OpenAI-compatible, etc.)."""

    provider_name: str = "base"

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        ...

    @abstractmethod
    async def list_models(self) -> List[str]:
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        ...


class ModelCapabilityRegistry:
    """Detects capabilities across Llama, Qwen, Gemma, Mistral, and OpenAI-compatible models."""

    FAMILY_PROFILES: Dict[str, Dict[str, Any]] = {
        "llama": {
            "context_window": 131072,
            "supports_streaming": True,
            "supports_structured_output": True,
            "supports_tools": True,
            "recommended_ram_gb": 8,
            "notes": "Llama 3.x family; strong instruction following and citation formatting.",
        },
        "qwen": {
            "context_window": 32768,
            "supports_streaming": True,
            "supports_structured_output": True,
            "supports_tools": True,
            "recommended_ram_gb": 8,
            "notes": "Qwen 2.5 family; strong multilingual, math, and technical reasoning.",
        },
        "gemma": {
            "context_window": 8192,
            "supports_streaming": True,
            "supports_structured_output": True,
            "supports_tools": False,
            "recommended_ram_gb": 6,
            "notes": "Gemma family; compact footprint, tools disabled by default.",
        },
        "mistral": {
            "context_window": 32768,
            "supports_streaming": True,
            "supports_structured_output": True,
            "supports_tools": True,
            "recommended_ram_gb": 8,
            "notes": "Mistral family; low-latency local inference.",
        },
    }

    @classmethod
    def detect_family(cls, model_name: str) -> str:
        lower = (model_name or "").lower()
        for fam in ("llama", "qwen", "gemma", "mistral", "deepseek", "gpt"):
            if fam in lower:
                return fam
        return "generic"

    @classmethod
    def get_capabilities(cls, model_name: str, provider: str = "ollama") -> ModelCapabilities:
        lower = (model_name or "").lower()
        is_embed = "embed" in lower or "nomic" in lower or "bge" in lower
        family = cls.detect_family(model_name)
        profile = cls.FAMILY_PROFILES.get(family, {})

        return ModelCapabilities(
            model_id=model_name,
            family=family,
            provider=provider,
            context_window=profile.get("context_window", 8192),
            supports_streaming=not is_embed and profile.get("supports_streaming", True),
            supports_structured_output=not is_embed and profile.get("supports_structured_output", True),
            supports_tools=not is_embed and profile.get("supports_tools", False),
            is_embedding_model=is_embed,
            recommended_ram_gb=profile.get("recommended_ram_gb", 8),
            notes=profile.get("notes", "Standard compatible model."),
        )

