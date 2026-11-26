"""Retrieval, generation, citation, and performance metric calculators."""

import math
from typing import Dict, List, Sequence, Set


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int = 5) -> float:
    if not relevant_ids:
        return 1.0 if not retrieved_ids[:k] else 0.0
    hits = len(set(retrieved_ids[:k]) & relevant_ids)
    return round(hits / len(relevant_ids), 4)


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int = 5) -> float:
    top = list(retrieved_ids[:k])
    if not top:
        return 1.0 if not relevant_ids else 0.0
    hits = len(set(top) & relevant_ids)
    return round(hits / len(top), 4)


def mean_reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Set[str]) -> float:
    if not relevant_ids:
        return 1.0 if not retrieved_ids else 0.0
    for idx, cid in enumerate(retrieved_ids, start=1):
        if cid in relevant_ids:
            return round(1.0 / idx, 4)
    return 0.0


def ndcg_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int = 5) -> float:
    if not relevant_ids:
        return 1.0 if not retrieved_ids[:k] else 0.0
    dcg = 0.0
    for idx, cid in enumerate(retrieved_ids[:k], start=1):
        if cid in relevant_ids:
            dcg += 1.0 / math.log2(idx + 1)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(idx + 1) for idx in range(1, ideal_hits + 1))
    return round(dcg / idcg, 4) if idcg > 0 else 0.0


def citation_precision(valid_citations: int, total_citations: int) -> float:
    if total_citations == 0:
        return 1.0
    return round(valid_citations / total_citations, 4)


def citation_recall(cited_relevant_ids: Set[str], expected_relevant_ids: Set[str]) -> float:
    if not expected_relevant_ids:
        return 1.0
    return round(len(cited_relevant_ids & expected_relevant_ids) / len(expected_relevant_ids), 4)


def unsupported_claim_rate(unsupported_count: int, total_claims: int) -> float:
    if total_claims == 0:
        return 0.0
    return round(unsupported_count / total_claims, 4)


def summarize_latencies(latencies_ms: Sequence[float]) -> Dict[str, float]:
    if not latencies_ms:
        return {"mean_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
    ordered = sorted(latencies_ms)
    p95_idx = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return {
        "mean_ms": round(sum(ordered) / len(ordered), 2),
        "p95_ms": round(ordered[p95_idx], 2),
        "max_ms": round(ordered[-1], 2),
    }

