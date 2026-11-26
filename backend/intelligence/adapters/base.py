"""Base adapter interfaces and safe fallback execution wrapper."""

import logging
from typing import Any, Callable, List, Optional, Protocol, TypeVar
from backend.intelligence.contracts import RetrievedPassage

logger = logging.getLogger("docnest.intelligence.adapters")
T = TypeVar("T")


class RetrievalPort(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        search_mode: str = "hybrid",
    ) -> List[RetrievedPassage]:
        ...


class RerankerPort(Protocol):
    def rerank(
        self,
        query: str,
        passages: List[RetrievedPassage],
        top_k: int = 5,
        min_score: float = 0.30,
    ) -> List[RetrievedPassage]:
        ...


class LLMGeneratorPort(Protocol):
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        ...


def execute_with_fallback(
    stage_name: str,
    primary_fn: Callable[[], T],
    fallback_fn: Callable[[], T],
    fallback_reasons: Optional[List[str]] = None,
) -> T:
    """Execute an enhancement stage and gracefully fall back on any exception."""
    try:
        return primary_fn()
    except Exception as exc:
        logger.warning("Intelligence stage '%s' failed (%s); falling back to baseline.", stage_name, exc)
        if fallback_reasons is not None:
            fallback_reasons.append(f"{stage_name}: {exc}")
        return fallback_fn()


async def execute_async_with_fallback(
    stage_name: str,
    primary_fn: Callable[[], Any],
    fallback_fn: Callable[[], Any],
    fallback_reasons: Optional[List[str]] = None,
) -> Any:
    """Async variant of safe stage execution with baseline fallback."""
    try:
        return await primary_fn()
    except Exception as exc:
        logger.warning("Async intelligence stage '%s' failed (%s); falling back to baseline.", stage_name, exc)
        if fallback_reasons is not None:
            fallback_reasons.append(f"{stage_name}: {exc}")
        return await fallback_fn()

