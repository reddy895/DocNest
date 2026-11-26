"""Context deduplication and section-aware reading-order grouping."""

from typing import Dict, List, Tuple
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.hybrid_retrieval.deduplicator import jaccard_similarity


class ContextOrganizer:
    """Removes duplicate paragraphs and orders selected chunks in logical reading order."""

    def __init__(self, dup_threshold: float = 0.85):
        self.dup_threshold = dup_threshold

    def deduplicate(self, passages: List[RetrievedPassage]) -> Tuple[List[RetrievedPassage], int]:
        kept: List[RetrievedPassage] = []
        removed = 0
        for p in passages:
            if any(jaccard_similarity(p.text, k.text) >= self.dup_threshold for k in kept):
                removed += 1
                continue
            kept.append(p)
        return kept, removed

    @staticmethod
    def order_by_document_and_page(passages: List[RetrievedPassage]) -> List[RetrievedPassage]:
        """Group passages by document (ordered by best score per doc), then page and chunk index."""
        best_doc_score: Dict[str, float] = {}
        for p in passages:
            score = p.rerank_score if p.rerank_score is not None else p.final_score
            if p.doc_id not in best_doc_score or score > best_doc_score[p.doc_id]:
                best_doc_score[p.doc_id] = score

        return sorted(
            passages,
            key=lambda p: (-best_doc_score.get(p.doc_id, 0.0), p.doc_id, p.page_number, p.chunk_index),
        )

