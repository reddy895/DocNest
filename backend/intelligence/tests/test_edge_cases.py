"""Edge-case tests for Intelligence Engine 2.0 resilience and latency bounds."""

import pytest

from backend.intelligence.contracts import AnswerDepth, ClaimStatus, RetrievedPassage
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine
from backend.intelligence.hybrid_retrieval.engine import HybridRetrievalEngine
from backend.intelligence.evaluation.runner import _InMemoryCorpusAdapter
from backend.intelligence.reranking.engine import RerankingEngine
from backend.intelligence.context_optimizer.engine import ContextOptimizationEngine
from backend.intelligence.answer_verification.claim_verifier import ClaimLevelVerifier
from backend.intelligence.answer_verification.policy import BoundedVerificationPolicy
from backend.intelligence.answer_verification.verifier import AnswerVerifier


def test_empty_and_whitespace_inputs_handled_safely():
    qi = QueryIntelligenceEngine()
    qa = qi.analyze("   ")
    assert qa.original_query == ""
    assert qa.resolved_query == ""

    hyb = HybridRetrievalEngine(base_adapter=_InMemoryCorpusAdapter())
    assert hyb.retrieve("   ") == []

    rr = RerankingEngine(use_cross_encoder=False)
    assert rr.rerank("query", []) == []

    ctx = ContextOptimizationEngine().optimize("query", [])
    assert ctx.passages == []
    assert ctx.total_tokens_estimated == 0


def test_claim_verifier_negation_contradiction_and_inference_qualification():
    passage = RetrievedPassage(
        chunk_id="c_neg",
        doc_id="d_neg",
        filename="Policy.pdf",
        page_number=1,
        text="External cloud APIs are not enabled by default in DocNest.",
    )
    verifier = ClaimLevelVerifier()

    contradicted = verifier.verify_claim(
        "External cloud APIs are enabled by default in DocNest.",
        [passage],
    )
    assert contradicted.status == ClaimStatus.CONTRADICTED

    partial = verifier.verify_claim(
        "DocNest prioritizes local privacy and avoids external cloud APIs.",
        [passage],
    )
    assert partial.status in (ClaimStatus.SUPPORTED, ClaimStatus.PARTIALLY_SUPPORTED)

    qualified, _ = verifier.filter_or_qualify_claims([partial], remove_unsupported=True)
    assert len(qualified) > 0


@pytest.mark.asyncio
async def test_bounded_verification_policy_respects_latency_limit():
    verifier = AnswerVerifier(min_faithfulness=0.95)
    policy = BoundedVerificationPolicy(verifier=verifier, max_retries=1, max_latency_ms=0.0)

    calls = 0

    async def slow_gen():
        nonlocal calls
        calls += 1
        return "Unverified statement with no matching tokens."

    ans, res, attempts = await policy.execute(
        "What is the latency?",
        [RetrievedPassage(chunk_id="p1", doc_id="d1", filename="Doc.pdf", page_number=1, text="Latency is 10ms.")],
        slow_gen,
    )
    assert attempts == 1  # max_latency_ms=0.0 prevents retry
    assert res.abstained is True
    assert "could not find sufficient verified evidence" in ans.lower()
