"""Threshold filtering and Maximal Marginal Relevance (MMR) diversity selection."""

from typing import List
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.hybrid_retrieval.deduplicator import jaccard_similarity


class RelevanceAndDiversityFilter:
    """Filters low-relevance passages and selects diverse, high-signal top-K results."""

    def __init__(self, lambda_param: float = 0.75):
        self.lambda_param = lambda_param

    def filter_and_diversify(
        self,
        passages: List[RetrievedPassage],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[RetrievedPassage]:
        eligible = [
            p for p in passages
            if (p.rerank_score if p.rerank_score is not None else p.final_score) >= min_score
        ]
        if not eligible:
            return []
        if len(eligible) <= top_k:
            return eligible

        selected: List[RetrievedPassage] = []
        remaining = list(eligible)

        while remaining and len(selected) < top_k:
            best_idx = 0
            best_mmr = float("-inf")
            for idx, cand in enumerate(remaining):
                rel = cand.rerank_score if cand.rerank_score is not None else cand.final_score
                max_sim = (
                    max(jaccard_similarity(cand.text, s.text) for s in selected)
                    if selected
                    else 0.0
                )
                mmr = self.lambda_param * rel - (1.0 - self.lambda_param) * max_sim
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = idx
            selected.append(remaining.pop(best_idx))

        return selected
