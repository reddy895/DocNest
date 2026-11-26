"""Claim-to-source alignment scorer verifying supporting passage relevance."""

import re
from typing import List
from backend.intelligence.contracts import RetrievedPassage, VerifiedCitation
from backend.intelligence.citation_verification.verifier import CITATION_PATTERN, CitationVerifier
from backend.intelligence.hybrid_retrieval.normalizer import tokenize


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "to", "of", "and",
    "in", "that", "it", "for", "on", "with", "as", "by", "at", "from", "or", "this",
}


class ClaimSourceAligner:
    """Verifies that the claim surrounding a citation aligns with the cited passage."""

    def __init__(self, min_alignment: float = 0.20):
        self.min_alignment = min_alignment
        self.verifier = CitationVerifier()

    @staticmethod
    def _content_tokens(text: str) -> set[str]:
        return {t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2}

    @staticmethod
    def _extract_numbers(text: str) -> set[str]:
        return set(re.findall(r"\b\d+(?:\.\d+)?%?", text or ""))

    def score_claim_alignment(self, claim: str, passage_text: str) -> float:
        claim_clean = CITATION_PATTERN.sub("", claim).strip()
        c_tokens = self._content_tokens(claim_clean)
        p_tokens = self._content_tokens(passage_text)
        if not c_tokens or not p_tokens:
            return 0.0

        token_overlap = len(c_tokens & p_tokens) / len(c_tokens)

        # Penalize if claim introduces numbers absent from passage
        c_nums = self._extract_numbers(claim_clean)
        p_nums = self._extract_numbers(passage_text)
        num_penalty = 0.0
        if c_nums:
            missing_nums = c_nums - p_nums
            if missing_nums:
                num_penalty = 0.35 * (len(missing_nums) / len(c_nums))

        return round(max(0.0, min(1.0, token_overlap - num_penalty)), 4)

    def verify_and_align(
        self,
        answer_text: str,
        passages: List[RetrievedPassage],
    ) -> List[VerifiedCitation]:
        # Split sentences while ignoring periods inside [Filename, p. X] citations
        protected = CITATION_PATTERN.sub(
            lambda m: m.group(0).replace(".", "__DOT__"),
            answer_text or "",
        )
        raw_sentences = [
            s.replace("__DOT__", ".").strip()
            for s in re.split(r"(?<=[.!?])\s+|\n+", protected)
            if s.strip()
        ]
        verified: List[VerifiedCitation] = []

        for sent in raw_sentences:
            base_checks = self.verifier.verify_answer_citations(sent, passages)
            for vc in base_checks:
                if not vc.is_valid:
                    verified.append(vc)
                    continue
                matched = next((p for p in passages if p.chunk_id == vc.chunk_id), None)
                if matched is None:
                    vc.is_valid = False
                    vc.reason = "Cited chunk missing."
                    verified.append(vc)
                    continue
                score = self.score_claim_alignment(sent, matched.text)
                vc.alignment_score = score
                if score < self.min_alignment:
                    vc.is_valid = False
                    vc.reason = f"Low claim-to-passage alignment ({score:.2f} < {self.min_alignment:.2f})."
                verified.append(vc)

        return verified
