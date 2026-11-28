"""Unified RerankingEngine combining cross-encoder, lexical scoring, and MMR diversity."""

import logging
from typing import List, Optional
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.reranking.cross_encoder_adapter import SafeCrossEncoderAdapter
from backend.intelligence.reranking.lexical_scorer import LightweightOverlapScorer
from backend.intelligence.reranking.filter import RelevanceAndDiversityFilter

logger = logging.getLogger("docnest.intelligence.reranking")


class RerankingEngine:
    """
    Ranks retrieved passages for direct answerability while preserving all source
    metadata and falling back gracefully to input candidates on failure.
    """

    def __init__(
        self,
        cross_encoder: Optional[SafeCrossEncoderAdapter] = None,
        lexical_scorer: Optional[LightweightOverlapScorer] = None,
        diversity_filter: Optional[RelevanceAndDiversityFilter] = None,
        use_cross_encoder: bool = True,
        allow_lexical_fallback: bool = True,
    ):
        self.cross_encoder = cross_encoder or SafeCrossEncoderAdapter()
        self.lexical_scorer = lexical_scorer if lexical_scorer is not None else LightweightOverlapScorer()
        self.diversity_filter = diversity_filter or RelevanceAndDiversityFilter()
        self.use_cross_encoder = use_cross_encoder
        self.allow_lexical_fallback = allow_lexical_fallback

    def rerank(
        self,
        query: str,
        passages: List[RetrievedPassage],
        top_k: int = 5,
        min_score: float = 0.25,
    ) -> List[RetrievedPassage]:
        if not passages:
            return []
        if not query.strip():
            return passages[:top_k]

        try:
            if self.use_cross_encoder:
                scored = self.cross_encoder.rerank(
                    query=query,
                    passages=passages,
                    top_k=max(top_k * 2, len(passages)),
                    min_score=0.0,
                )
            elif self.allow_lexical_fallback and self.lexical_scorer is not None:
                scored = self.lexical_scorer.score_batch(query, passages)
            else:
                # Retain original retrieval order without inventing relevance scores
                return [p.model_copy(deep=True) for p in passages[:top_k]]

            filtered = self.diversity_filter.filter_and_diversify(
                scored, top_k=top_k, min_score=min_score
            )
            return filtered if filtered else scored[:top_k]
        except Exception as exc:
            logger.warning("RerankingEngine failed (%s); returning original passages.", exc)
            return passages[:top_k]

