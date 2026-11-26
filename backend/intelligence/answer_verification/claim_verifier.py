"""Module 6: Claim-Level Verification — breaks answers into claims and verifies each against evidence."""

import re
from typing import List, Tuple
from backend.intelligence.contracts import ClaimStatus, ClaimVerificationItem, RetrievedPassage
from backend.intelligence.citation_verification.aligner import ClaimSourceAligner
from backend.intelligence.citation_verification.verifier import CITATION_PATTERN


class ClaimLevelVerifier:
    """
    Decomposes generated answers into factual claims, checks each against retrieved
    evidence, and classifies them as Supported, Partially Supported, Unsupported, or Contradicted.
    """

    NEGATION_RE = re.compile(r"\b(no|not|never|none|neither|without|fails?\s+to|cannot)\b", re.IGNORECASE)

    def __init__(
        self,
        supported_threshold: float = 0.40,
        partial_threshold: float = 0.18,
    ):
        self.supported_threshold = supported_threshold
        self.partial_threshold = partial_threshold
        self.aligner = ClaimSourceAligner()

    @staticmethod
    def split_claims(answer_text: str) -> List[str]:
        protected = CITATION_PATTERN.sub(
            lambda m: m.group(0).replace(".", "__DOT__"),
            answer_text or "",
        )
        raw = [
            s.replace("__DOT__", ".").strip()
            for s in re.split(r"(?<=[.!?])\s+|\n+", protected)
            if s.strip()
        ]
        # Skip short Markdown headings
        return [c for c in raw if len(c) > 15 and not c.startswith("#")]

    def verify_claim(
        self,
        claim: str,
        passages: List[RetrievedPassage],
    ) -> ClaimVerificationItem:
        if not passages:
            return ClaimVerificationItem(
                claim=claim,
                status=ClaimStatus.UNSUPPORTED,
                evidence_score=0.0,
                reason="No retrieved passages available.",
            )

        best_score = 0.0
        best_passage: RetrievedPassage | None = None
        for p in passages:
            score = self.aligner.score_claim_alignment(claim, p.text)
            if score > best_score:
                best_score = score
                best_passage = p

        # Check for numerical or negation contradiction against best matching passage
        if best_passage is not None:
            c_nums = self.aligner._extract_numbers(CITATION_PATTERN.sub("", claim))
            p_nums = self.aligner._extract_numbers(best_passage.text)
            if c_nums and p_nums and (c_nums - p_nums) and best_score >= self.partial_threshold:
                return ClaimVerificationItem(
                    claim=claim,
                    status=ClaimStatus.CONTRADICTED,
                    evidence_score=best_score,
                    supporting_chunk_id=best_passage.chunk_id,
                    reason=f"Claim numbers {sorted(c_nums)} conflict with source numbers {sorted(p_nums)}.",
                )

            claim_neg = bool(self.NEGATION_RE.search(claim))
            pass_neg = bool(self.NEGATION_RE.search(best_passage.text))
            if claim_neg != pass_neg and best_score >= 0.55:
                return ClaimVerificationItem(
                    claim=claim,
                    status=ClaimStatus.CONTRADICTED,
                    evidence_score=best_score,
                    supporting_chunk_id=best_passage.chunk_id,
                    reason="Polarity/negation mismatch with best matching source passage.",
                )

        if best_score >= self.supported_threshold:
            return ClaimVerificationItem(
                claim=claim,
                status=ClaimStatus.SUPPORTED,
                evidence_score=best_score,
                supporting_chunk_id=best_passage.chunk_id if best_passage else None,
            )
        if best_score >= self.partial_threshold:
            return ClaimVerificationItem(
                claim=claim,
                status=ClaimStatus.PARTIALLY_SUPPORTED,
                evidence_score=best_score,
                supporting_chunk_id=best_passage.chunk_id if best_passage else None,
                reason="Partial lexical/concept overlap with source passage.",
            )
        return ClaimVerificationItem(
            claim=claim,
            status=ClaimStatus.UNSUPPORTED,
            evidence_score=best_score,
            reason="Insufficient overlap with retrieved passages.",
        )

    def verify_answer(
        self,
        answer_text: str,
        passages: List[RetrievedPassage],
    ) -> List[ClaimVerificationItem]:
        claims = self.split_claims(answer_text)
        return [self.verify_claim(c, passages) for c in claims]

    def filter_or_qualify_claims(
        self,
        items: List[ClaimVerificationItem],
        remove_unsupported: bool = True,
    ) -> Tuple[str, List[ClaimVerificationItem]]:
        """
        Keep Supported claims as-is, qualify Partially Supported claims as [Inference],
        and remove or flag Unsupported/Contradicted claims.
        """
        kept_lines: List[str] = []
        for item in items:
            if item.status == ClaimStatus.SUPPORTED:
                kept_lines.append(item.claim)
            elif item.status == ClaimStatus.PARTIALLY_SUPPORTED:
                kept_lines.append(f"[Inference] {item.claim}")
            elif not remove_unsupported and item.status == ClaimStatus.UNSUPPORTED:
                kept_lines.append(f"[Unverified] {item.claim}")
        return " ".join(kept_lines), items
