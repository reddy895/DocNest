"""Bounded verification retry policy and honest uncertainty response builder."""

import time
from typing import Awaitable, Callable, List, Tuple
from backend.intelligence.contracts import AnswerVerificationResult, RetrievedPassage
from backend.intelligence.answer_verification.verifier import AnswerVerifier


def build_uncertainty_response(question: str, notes: List[str] | None = None) -> str:
    detail = f" ({'; '.join(notes)})" if notes else ""
    return (
        "I could not find sufficient verified evidence in the uploaded documents "
        f"to answer \"{question}\" with high confidence{detail}. "
        "Please verify with the original source documents or upload additional context."
    )


class BoundedVerificationPolicy:
    """
    Executes generation + verification with at most 1 bounded retry,
    respecting configured latency limits and returning an honest uncertainty
    response if verification still fails.
    """

    def __init__(
        self,
        verifier: AnswerVerifier | None = None,
        max_retries: int = 1,
        max_latency_ms: float = 15000.0,
    ):
        self.verifier = verifier or AnswerVerifier()
        self.max_retries = max(0, min(max_retries, 1))
        self.max_latency_ms = max_latency_ms

    async def execute(
        self,
        question: str,
        passages: List[RetrievedPassage],
        generate_fn: Callable[[], Awaitable[str]],
    ) -> Tuple[str, AnswerVerificationResult, int]:
        """Return (final_answer, verification_result, attempts_used)."""
        start = time.perf_counter()
        attempts = 0
        last_answer = ""
        last_result = AnswerVerificationResult()

        for attempt in range(self.max_retries + 1):
            elapsed_ms = (time.perf_counter() - start) * 1000
            if attempt > 0 and elapsed_ms >= self.max_latency_ms:
                break

            attempts += 1
            last_answer = await generate_fn()
            last_result = self.verifier.verify(question, last_answer, passages)
            if not last_result.needs_retry:
                return last_answer, last_result, attempts

        if last_result.needs_retry and not last_result.abstained:
            uncertainty = build_uncertainty_response(question, last_result.notes)
            last_result.abstained = True
            return uncertainty, last_result, attempts

        return last_answer, last_result, attempts
