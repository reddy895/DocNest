"""Module 1: Strict Evidence-Based Answering & Pre-Generation Sufficiency Check."""

import re
from typing import Dict, List, Set, Tuple
from backend.intelligence.contracts import EvidenceSufficiencyResult, RetrievedPassage
from backend.intelligence.hybrid_retrieval.normalizer import tokenize


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "to", "of", "and",
    "in", "that", "it", "for", "on", "with", "as", "by", "at", "from", "or", "this",
    "what", "which", "who", "how", "why", "when", "where", "does", "do", "did", "can",
    "explain", "describe", "tell", "me", "about", "using", "used", "give",
}


class EvidenceSufficiencyChecker:
    """
    Checks whether retrieved passages contain sufficient evidence to answer
    a query before generation, and detects potential cross-source contradictions.
    """

    def __init__(self, min_coverage: float = 0.28):
        self.min_coverage = min_coverage

    @staticmethod
    def _key_terms(text: str) -> Set[str]:
        return {t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2}

    @staticmethod
    def detect_contradictions(passages: List[RetrievedPassage]) -> List[str]:
        """
        Detect conflicting numeric values associated with the same metric/entity
        across distinct passages.
        """
        metric_values: Dict[str, Set[str]] = {}
        pattern = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_-]{2,})\s+(?:is|was|reached|achieved|of|=|:)\s+(\$?\d+(?:\.\d+)?%?(?:ms|M|B|K)?)\b", re.IGNORECASE)
        for p in passages:
            for match in pattern.finditer(p.text or ""):
                key = match.group(1).lower()
                val = match.group(2).lower()
                metric_values.setdefault(key, set()).add(val)

        contradictions: List[str] = []
        for metric, vals in metric_values.items():
            if len(vals) > 1:
                sorted_vals = ", ".join(sorted(vals))
                contradictions.append(f"Conflicting values for '{metric}': {sorted_vals}")
        return contradictions

    def check(self, query: str, passages: List[RetrievedPassage]) -> EvidenceSufficiencyResult:
        if not passages:
            return EvidenceSufficiencyResult(
                is_sufficient=False,
                coverage_score=0.0,
                missing_aspects=["No relevant document passages retrieved."],
                needs_additional_retrieval=True,
            )

        q_terms = self._key_terms(query)
        combined = " ".join(p.text for p in passages)
        p_terms = self._key_terms(combined)

        if not q_terms:
            return EvidenceSufficiencyResult(is_sufficient=True, coverage_score=1.0)

        matched = q_terms & p_terms
        missing = sorted(q_terms - p_terms)
        coverage = round(len(matched) / len(q_terms), 4)
        contradictions = self.detect_contradictions(passages)

        is_sufficient = coverage >= self.min_coverage
        return EvidenceSufficiencyResult(
            is_sufficient=is_sufficient,
            coverage_score=coverage,
            missing_aspects=missing[:8],
            contradictions_detected=contradictions,
            needs_additional_retrieval=not is_sufficient,
        )


def build_missing_evidence_response(query: str, missing_aspects: List[str] | None = None) -> str:
    missing_note = ""
    if missing_aspects:
        missing_note = f" Missing concepts in retrieved sources: {', '.join(missing_aspects[:5])}."
    return (
        "The uploaded documents do not contain sufficient evidence to answer "
        f"\"{query}\".{missing_note} "
        "Please upload additional relevant sections or documents."
    )


def build_strict_evidence_system_prompt() -> str:
    return (
        "You are DocNest, an evidence-grounded research assistant.\n"
        "NON-NEGOTIABLE EVIDENCE RULES:\n"
        "1. Use ONLY the retrieved document passages as evidence.\n"
        "2. NEVER invent project details, technologies, statistics, results, or implementation steps.\n"
        "3. NEVER assume a technology was used just because it is common in similar projects.\n"
        "4. NEVER fabricate citations or page numbers; cite inline as [Filename, p. X].\n"
        "5. Clearly distinguish document-supported facts from any interpretation (label interpretations as [Interpretation]).\n"
        "6. If information is missing from the documents, explicitly state it was not found in the uploaded documents.\n"
        "7. If retrieved sources contradict each other, explicitly highlight the contradiction.\n"
        "8. Do NOT use general LLM knowledge to silently fill gaps."
    )

