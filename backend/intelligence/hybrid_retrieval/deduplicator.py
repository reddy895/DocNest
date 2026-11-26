"""Passage deduplication and embedding-dimension safety guard."""

from typing import List, Optional, Set
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.hybrid_retrieval.normalizer import tokenize


def jaccard_similarity(a: str, b: str) -> float:
    sa = set(tokenize(a))
    sb = set(tokenize(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class PassageDeduplicator:
    """Removes exact chunk_id duplicates and near-duplicate text passages."""

    def __init__(self, similarity_threshold: float = 0.88):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, passages: List[RetrievedPassage]) -> List[RetrievedPassage]:
        seen_ids: Set[str] = set()
        kept: List[RetrievedPassage] = []

        for p in passages:
            if p.chunk_id in seen_ids:
                continue
            is_near_dup = any(
                jaccard_similarity(p.text, existing.text) >= self.similarity_threshold
                for existing in kept
            )
            if is_near_dup:
                continue
            seen_ids.add(p.chunk_id)
            kept.append(p)

        return kept


def assert_compatible_embedding_dim(
    expected_dim: int,
    candidate_dim: Optional[int],
    collection_name: str = "docnest_collection",
) -> None:
    """Prevent silently mixing incompatible vector dimensions."""
    if candidate_dim is not None and candidate_dim != expected_dim:
        raise ValueError(
            f"Incompatible embedding dimension {candidate_dim} for collection "
            f"'{collection_name}' (expected {expected_dim})."
        )
