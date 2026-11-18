import logging
import math
from typing import List, Optional, Tuple
from sentence_transformers import CrossEncoder

from backend.app.core.config import settings
from backend.app.services.retrieval_service import RetrievalCandidate

logger = logging.getLogger("docnest.reranker")


def sigmoid(x: float) -> float:
    """Normalize raw logit to [0, 1] probability range."""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


class CrossEncoderReranker:
    """
    Singleton Cross-Encoder reranker evaluating query-document relevance.
    Employs ms-marco-MiniLM-L-6-v2 on CPU with sigmoid score normalization
    and strict confidence filtering.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL
        self._model: Optional[CrossEncoder] = None

    def _ensure_model(self) -> CrossEncoder:
        if self._model is None:
            logger.info(f"Loading CrossEncoder reranker model '{self.model_name}' on CPU...")
            self._model = CrossEncoder(self.model_name, max_length=512)
            logger.info("CrossEncoder reranker loaded successfully.")
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        top_k: int = 5,
        min_relevance_score: float = 0.30,
    ) -> List[RetrievalCandidate]:
        """
        Rerank a list of retrieval candidates against the query string.
        Returns candidates scoring >= min_relevance_score, sorted descending, up to top_k.
        """
        if not candidates or not query.strip():
            return []

        model = self._ensure_model()
        pairs = [[query, c.text] for c in candidates]

        # Predict logits
        logits = model.predict(pairs, show_progress_bar=False)

        scored_candidates: List[RetrievalCandidate] = []
        for candidate, raw_logit in zip(candidates, logits):
            normalized_score = sigmoid(float(raw_logit))
            candidate.reranker_score = round(normalized_score, 4)

            if normalized_score >= min_relevance_score:
                scored_candidates.append(candidate)

        # Sort descending by reranker score
        scored_candidates.sort(key=lambda c: c.reranker_score or 0.0, reverse=True)
        return scored_candidates[:top_k]


# Singleton instance
_reranker_instance: Optional[CrossEncoderReranker] = None


def get_reranker() -> CrossEncoderReranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker()
    return _reranker_instance
