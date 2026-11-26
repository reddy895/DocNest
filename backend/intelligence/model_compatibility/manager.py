"""Model Compatibility Manager with provider routing and embedding-collection safety guard."""

from typing import Dict, List, Optional
from backend.intelligence.model_compatibility.registry import (
    LLMProvider,
    ModelCapabilities,
    ModelCapabilityRegistry,
    ProviderHealth,
)
from backend.intelligence.model_compatibility.ollama_adapter import OllamaProviderAdapter
from backend.intelligence.model_compatibility.openai_adapter import OpenAICompatibleAdapter


class EmbeddingCollectionMismatchError(ValueError):
    """Raised when an embedding model change would conflict with an existing collection."""


class ModelCompatibilityManager:
    """
    Manages isolated LLM providers, capability inspection, and embedding safety checks.
    Keeps embedding models strictly separate from generation models.
    """

    def __init__(
        self,
        providers: Optional[Dict[str, LLMProvider]] = None,
        active_embedding_model: str = "nomic-embed-text",
        active_collection_name: str = "docnest_collection",
    ):
        self.providers: Dict[str, LLMProvider] = providers or {
            "ollama": OllamaProviderAdapter(),
            "openai_compatible": OpenAICompatibleAdapter(),
        }
        self.active_embedding_model = active_embedding_model
        self.active_collection_name = active_collection_name

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        self.providers[name] = provider

    def get_provider(self, name: str) -> LLMProvider:
        if name not in self.providers:
            raise KeyError(f"Unknown model provider: {name}")
        return self.providers[name]

    def inspect_model(self, model_name: str, provider: str = "ollama") -> ModelCapabilities:
        return ModelCapabilityRegistry.get_capabilities(model_name, provider=provider)

    def validate_embedding_change(
        self,
        new_embedding_model: str,
        target_collection_name: str,
    ) -> None:
        """
        Ensure changing an embedding model never silently reuses a collection built
        with a different embedding model.
        """
        if (
            new_embedding_model != self.active_embedding_model
            and target_collection_name == self.active_collection_name
        ):
            raise EmbeddingCollectionMismatchError(
                f"Cannot reuse collection '{target_collection_name}' when switching "
                f"embedding model from '{self.active_embedding_model}' to '{new_embedding_model}'. "
                "Create or target a dedicated collection for the new embedding space."
            )

    async def check_all_providers(self) -> Dict[str, ProviderHealth]:
        results: Dict[str, ProviderHealth] = {}
        for name, prov in self.providers.items():
            results[name] = await prov.check_health()
        return results

    async def list_compatible_generation_models(self, provider: str = "ollama") -> List[ModelCapabilities]:
        prov = self.get_provider(provider)
        models = await prov.list_models()
        caps = [self.inspect_model(m, provider=provider) for m in models]
        return [c for c in caps if not c.is_embedding_model]
