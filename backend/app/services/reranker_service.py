import gc
import logging
import math
from typing import List, Optional, Tuple
import torch
from sentence_transformers import CrossEncoder

from backend.app.core.config import settings
from backend.app.services.retrieval_service import RetrievalCandidate

logger = logging.getLogger("docnest.reranker")

# Configure optimal thread utilization for 12GB CPU target
if torch.get_num_threads() > 4:
    torch.set_num_threads(4)


def sigmoid(x: float) -> float:
    """Normalize raw logit to [0, 1] probability range."""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


class CrossEncoderReranker:
    """
    Singleton Cross-Encoder reranker evaluating query-document relevance.
    Optimized for 12GB RAM environments using batched CPU inference,
    torch.inference_mode, and passage truncation.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL
        self._model: Optional[CrossEncoder] = None
        self.batch_size = 16

    def _ensure_model(self) -> CrossEncoder:
        if self._model is None:
            logger.info(f"Loading CrossEncoder reranker model '{self.model_name}' on CPU...")
            self._model = CrossEncoder(self.model_name, max_length=384, device="cpu")
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
        Rerank a list of retrieval candidates against the query string with
        memory-efficient batching and inference_mode.
        """
        if not candidates or not query.strip():
            return []

        model = self._ensure_model()
        # Truncate passage text to 400 chars to avoid large attention matrix memory spikes
        pairs = [[query, c.text[:400]] for c in candidates]

        with torch.inference_mode():
            logits = model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

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
