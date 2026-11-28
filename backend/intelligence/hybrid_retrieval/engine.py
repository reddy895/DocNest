"""Optional Hybrid Retrieval Engine wrapping existing DocNest retriever."""

import logging
from typing import List, Optional, Tuple
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.adapters.existing_rag_adapter import ExistingRetrieverAdapter
from backend.intelligence.hybrid_retrieval.filters import MetadataFilterEngine
from backend.intelligence.hybrid_retrieval.fusion import WeightedHybridFusion
from backend.intelligence.hybrid_retrieval.deduplicator import PassageDeduplicator

logger = logging.getLogger("docnest.intelligence.hybrid_retrieval")


class HybridRetrievalEngine:
    """
    Enhances existing semantic + BM25 retrieval results with configurable weighted
    fusion, metadata filtering, sub-query merging, and deduplication.
    """

    def __init__(
        self,
        base_adapter: Optional[ExistingRetrieverAdapter] = None,
        fusion: Optional[WeightedHybridFusion] = None,
        deduplicator: Optional[PassageDeduplicator] = None,
    ):
        self.base_adapter = base_adapter or ExistingRetrieverAdapter()
        self.fusion = fusion or WeightedHybridFusion()
        self.deduplicator = deduplicator or PassageDeduplicator()

    def retrieve(
        self,
        query: str,
        expanded_terms: Optional[List[str]] = None,
        sub_queries: Optional[List[str]] = None,
        top_k: int = 20,
        doc_ids: Optional[List[str]] = None,
        page_numbers: Optional[List[int]] = None,
        page_range: Optional[Tuple[int, int]] = None,
        workspace_id: Optional[str] = None,
        section_query: Optional[str] = None,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
    ) -> List[RetrievedPassage]:
        queries_to_run = [q for q in (sub_queries or [query]) if q and q.strip()]
        if not queries_to_run:
            return []

        fusion = (
            WeightedHybridFusion(dense_weight=dense_weight, sparse_weight=sparse_weight)
            if (dense_weight is not None and sparse_weight is not None)
            else self.fusion
        )

        try:
            result_sets: List[List[RetrievedPassage]] = []
            for q in queries_to_run[:4]:
                raw = self.base_adapter.retrieve(
                    query=q,
                    top_k=max(top_k, 20),
                    doc_ids=doc_ids,
                    workspace_id=workspace_id,
                    search_mode="hybrid",
                )
                fused = fusion.fuse(q, raw, expanded_terms=expanded_terms)
                result_sets.append(fused)

            merged = (
                fusion.merge_multi_query_results(result_sets)
                if len(result_sets) > 1
                else result_sets[0]
            )

            filtered = MetadataFilterEngine.apply_filters(
                merged,
                doc_ids=doc_ids,
                page_numbers=page_numbers,
                page_range=page_range,
                workspace_id=workspace_id,
                section_query=section_query,
            )

            deduped = self.deduplicator.deduplicate(filtered)
            return deduped[:top_k]
        except Exception as exc:
            logger.warning("HybridRetrievalEngine failed (%s); falling back to base retriever.", exc)
            return self.base_adapter.retrieve(
                query=query,
                top_k=top_k,
                doc_ids=doc_ids,
                workspace_id=workspace_id,
            )[:top_k]

