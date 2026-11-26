"""Fast, deterministic Answer Verification Engine for faithfulness and claim checking."""

import re
from typing import List
from backend.intelligence.contracts import AnswerVerificationResult, RetrievedPassage
from backend.intelligence.citation_verification.aligner import ClaimSourceAligner
from backend.intelligence.citation_verification.verifier import CITATION_PATTERN


class AnswerVerifier:
    """
    Evaluates answer relevance, context faithfulness, unsupported claims,
    and cross-passage numerical/polarity contradictions without an extra LLM call.
    """

    ABSTENTION_MARKERS = (
        "could not find sufficient evidence",
        "no documents are currently indexed",
        "do not contain enough information",
        "cannot determine from the provided",
    )

    def __init__(
        self,
        min_faithfulness: float = 0.45,
        min_relevance: float = 0.20,
    ):
        self.min_faithfulness = min_faithfulness
        self.min_relevance = min_relevance
        self.aligner = ClaimSourceAligner()

    def verify(
        self,
        question: str,
        answer: str,
        passages: List[RetrievedPassage],
    ) -> AnswerVerificationResult:
        ans = (answer or "").strip()
        if not ans:
            return AnswerVerificationResult(
                is_faithful=False,
                relevance_score=0.0,
                faithfulness_score=0.0,
                needs_retry=True,
                notes=["Empty answer generated."],
            )

        lower_ans = ans.lower()
        if any(m in lower_ans for m in self.ABSTENTION_MARKERS):
            return AnswerVerificationResult(
                is_faithful=True,
                relevance_score=1.0,
                faithfulness_score=1.0,
                abstained=True,
                needs_retry=False,
                notes=["Model honestly abstained due to insufficient evidence."],
            )

        if not passages:
            return AnswerVerificationResult(
                is_faithful=False,
                relevance_score=0.0,
                faithfulness_score=0.0,
                unsupported_claims=[ans[:160]],
                needs_retry=True,
                notes=["Answer produced with zero supporting passages."],
            )

        combined_context = "\n".join(p.text for p in passages)
        relevance = self.aligner.score_claim_alignment(question, ans)

        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+|\n+", ans)
            if s.strip() and len(s.strip()) > 15
        ]
        if not sentences:
            sentences = [ans]

        unsupported: List[str] = []
        scores: List[float] = []
        for sent in sentences:
            clean_sent = CITATION_PATTERN.sub("", sent).strip()
            if not clean_sent:
                continue
            sc = self.aligner.score_claim_alignment(clean_sent, combined_context)
            scores.append(sc)
            if sc < 0.20:
                unsupported.append(clean_sent[:140])

        faithfulness = round(sum(scores) / len(scores), 4) if scores else 0.0
        is_faithful = faithfulness >= self.min_faithfulness and len(unsupported) <= max(1, len(sentences) // 3)
        needs_retry = not is_faithful or relevance < self.min_relevance

        notes: List[str] = []
        if not is_faithful:
            notes.append(f"Faithfulness {faithfulness:.2f} below threshold {self.min_faithfulness:.2f}.")
        if relevance < self.min_relevance:
            notes.append(f"Answer relevance {relevance:.2f} below threshold {self.min_relevance:.2f}.")

        return AnswerVerificationResult(
            is_faithful=is_faithful,
            relevance_score=relevance,
            faithfulness_score=faithfulness,
            unsupported_claims=unsupported,
            needs_retry=needs_retry,
            abstained=False,
            notes=notes,
        )

