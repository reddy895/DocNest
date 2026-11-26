"""Weighted Reciprocal Rank Fusion and score blending for hybrid retrieval."""

from typing import Dict, List
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.hybrid_retrieval.normalizer import compute_keyword_score, normalize_passages


class WeightedHybridFusion:
    """Combines dense, sparse, and query-expanded keyword signals with configurable weights."""

    def __init__(
        self,
        dense_weight: float = 0.55,
        sparse_weight: float = 0.30,
        keyword_weight: float = 0.15,
        rrf_k: int = 60,
    ):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k

    def fuse(
        self,
        query: str,
        passages: List[RetrievedPassage],
        expanded_terms: List[str] | None = None,
    ) -> List[RetrievedPassage]:
        if not passages:
            return []

        normed = normalize_passages(passages)
        fused: List[RetrievedPassage] = []

        for p in normed:
            dense_sig = p.dense_score if p.dense_score is not None else (
                1.0 / (self.rrf_k + p.dense_rank) if p.dense_rank else 0.0
            )
            sparse_sig = p.sparse_score if p.sparse_score is not None else (
                1.0 / (self.rrf_k + p.sparse_rank) if p.sparse_rank else 0.0
            )
            kw_sig = compute_keyword_score(query, p.text, expanded_terms=expanded_terms)

            blended = (
                self.dense_weight * dense_sig
                + self.sparse_weight * sparse_sig
                + self.keyword_weight * kw_sig
                + 0.10 * p.rrf_score
            )
            p.final_score = round(min(max(blended, 0.0), 1.5), 4)
            fused.append(p)

        fused.sort(key=lambda item: item.final_score, reverse=True)
        return fused

    @staticmethod
    def merge_multi_query_results(
        result_sets: List[List[RetrievedPassage]],
    ) -> List[RetrievedPassage]:
        """Merge passages retrieved across decomposed sub-queries, keeping max score per chunk."""
        by_chunk: Dict[str, RetrievedPassage] = {}
        for rset in result_sets:
            for p in rset:
                existing = by_chunk.get(p.chunk_id)
                if existing is None or p.final_score > existing.final_score:
                    by_chunk[p.chunk_id] = p
        merged = list(by_chunk.values())
        merged.sort(key=lambda item: item.final_score, reverse=True)
        return merged

