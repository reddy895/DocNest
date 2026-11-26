"""Result normalization and lightweight keyword scoring for hybrid retrieval."""

import math
import re
from typing import Dict, List
from backend.intelligence.contracts import RetrievedPassage


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_-]+", (text or "").lower())


def min_max_normalize(scores: List[float]) -> List[float]:
    if not scores:
        return []
    lo = min(scores)
    hi = max(scores)
    if math.isclose(hi, lo, rel_tol=1e-9, abs_tol=1e-9):
        return [1.0 if hi > 0 else 0.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def normalize_passages(passages: List[RetrievedPassage]) -> List[RetrievedPassage]:
    """Normalize dense, sparse, and rrf scores into [0, 1] without mutating metadata."""
    if not passages:
        return []

    dense_vals = [p.dense_score if p.dense_score is not None else 0.0 for p in passages]
    sparse_vals = [p.sparse_score if p.sparse_score is not None else 0.0 for p in passages]
    rrf_vals = [p.rrf_score for p in passages]

    norm_dense = min_max_normalize(dense_vals) if any(v > 0 for v in dense_vals) else dense_vals
    norm_sparse = min_max_normalize(sparse_vals) if any(v > 0 for v in sparse_vals) else sparse_vals
    norm_rrf = min_max_normalize(rrf_vals) if any(v > 0 for v in rrf_vals) else rrf_vals

    normalized: List[RetrievedPassage] = []
    for p, nd, ns, nr in zip(passages, norm_dense, norm_sparse, norm_rrf):
        copy = p.model_copy(deep=True)
        if copy.dense_score is not None:
            copy.dense_score = round(nd, 4)
        if copy.sparse_score is not None:
            copy.sparse_score = round(ns, 4)
        copy.rrf_score = round(nr, 4)
        normalized.append(copy)
    return normalized


def compute_keyword_score(query: str, text: str, expanded_terms: List[str] | None = None) -> float:
    """Compute TF-weighted keyword overlap score between query (+ expansions) and passage."""
    q_tokens = set(tokenize(query))
    if expanded_terms:
        for term in expanded_terms:
            q_tokens.update(tokenize(term))
    if not q_tokens:
        return 0.0

    doc_tokens = tokenize(text)
    if not doc_tokens:
        return 0.0

    tf: Dict[str, int] = {}
    for tok in doc_tokens:
        tf[tok] = tf.get(tok, 0) + 1

    hits = sum(1.0 + math.log1p(tf[t]) for t in q_tokens if t in tf)
    return round(hits / max(len(q_tokens), 1), 4)

