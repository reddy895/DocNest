"""Cross-Encoder adapter with lazy evaluation and graceful lexical fallback."""

import logging
from typing import List, Optional
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.adapters.existing_rag_adapter import ExistingRerankerAdapter
from backend.intelligence.reranking.lexical_scorer import LightweightOverlapScorer

logger = logging.getLogger("docnest.intelligence.reranking")


class SafeCrossEncoderAdapter:
    """
    Wraps existing CrossEncoder reranker with fallback to lightweight lexical scoring
    if model loading or inference fails. Preserves all passage metadata.
    """

    def __init__(
        self,
        base_reranker: Optional[ExistingRerankerAdapter] = None,
        lexical_fallback: Optional[LightweightOverlapScorer] = None,
    ):
        self.base_reranker = base_reranker or ExistingRerankerAdapter()
        self.lexical_fallback = lexical_fallback or LightweightOverlapScorer()

    def rerank(
        self,
        query: str,
        passages: List[RetrievedPassage],
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> List[RetrievedPassage]:
        if not passages or not query.strip():
            return passages[:top_k]

        try:
            ranked = self.base_reranker.rerank(
                query=query,
                passages=passages,
                top_k=max(top_k, len(passages)),
                min_score=min_score,
            )
            if ranked:
                return ranked[:top_k]
        except Exception as exc:
            logger.warning("CrossEncoder adapter failed (%s); falling back to lexical scorer.", exc)

        return self.lexical_fallback.score_batch(query, passages)[:top_k]

