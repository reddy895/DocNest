"""Lightweight lexical and structural overlap scorer for fast passage reranking."""

from typing import List
from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.hybrid_retrieval.normalizer import tokenize


class LightweightOverlapScorer:
    """
    Computes deterministic relevance scores using unigram coverage, bigram overlap,
    and section heading alignment without GPU or heavy model overhead.
    """

    def score_passage(self, query: str, passage: RetrievedPassage) -> float:
        q_tokens = tokenize(query)
        if not q_tokens or not passage.text.strip():
            return 0.0

        p_tokens = tokenize(passage.text)
        p_set = set(p_tokens)
        q_set = set(q_tokens)

        # Unigram coverage
        unigram_cov = len(q_set & p_set) / len(q_set)

        # Bigram phrase match bonus
        q_bigrams = set(zip(q_tokens, q_tokens[1:])) if len(q_tokens) > 1 else set()
        p_bigrams = set(zip(p_tokens, p_tokens[1:])) if len(p_tokens) > 1 else set()
        bigram_cov = (len(q_bigrams & p_bigrams) / len(q_bigrams)) if q_bigrams else 0.0

        # Section heading alignment bonus
        heading_cov = 0.0
        if passage.section_heading:
            h_set = set(tokenize(passage.section_heading))
            if h_set:
                heading_cov = len(q_set & h_set) / len(q_set)

        combined = 0.65 * unigram_cov + 0.25 * bigram_cov + 0.10 * heading_cov
        return round(min(max(combined, 0.0), 1.0), 4)

    def score_batch(self, query: str, passages: List[RetrievedPassage]) -> List[RetrievedPassage]:
        scored: List[RetrievedPassage] = []
        for p in passages:
            copy = p.model_copy(deep=True)
            lex_score = self.score_passage(query, copy)
            copy.rerank_score = lex_score
            copy.final_score = round(0.55 * lex_score + 0.45 * copy.final_score, 4)
            scored.append(copy)
        scored.sort(key=lambda item: item.final_score, reverse=True)
        return scored
