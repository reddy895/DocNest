"""Tests for Hallucination Reduction, Deep Project Understanding, and Multi-Stage Pipeline."""

import pytest

from backend.intelligence.contracts import AnswerDepth, ClaimStatus, RetrievedPassage
from backend.intelligence.answer_verification.evidence_grounding import (
    EvidenceSufficiencyChecker,
    build_missing_evidence_response,
)
from backend.intelligence.project_intelligence.engine import ProjectIntelligenceEngine
from backend.intelligence.context_optimizer.depth_controls import resolve_answer_depth
from backend.intelligence.query_intelligence.rewriter import ConversationQueryRewriter
from backend.intelligence.answer_verification.claim_verifier import ClaimLevelVerifier
from backend.intelligence.answer_verification.completeness import AnswerCompletenessChecker
from backend.intelligence.hybrid_retrieval.engine import HybridRetrievalEngine
from backend.intelligence.evaluation.runner import _InMemoryCorpusAdapter
from backend.intelligence.evaluation.hallucination_benchmark import (
    PROJECT_CORPUS,
    build_hallucination_benchmark_dataset,
    run_hallucination_benchmark,
)
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.multi_stage_retrieval import MultiStagePipeline


def test_evidence_sufficiency_and_contradiction_detection():
    checker = EvidenceSufficiencyChecker(min_coverage=0.35)
    passages = [
        RetrievedPassage(
            chunk_id="p1",
            doc_id="d1",
            filename="A.pdf",
            page_number=1,
            text="Latency was 42ms in benchmark tests.",
        ),
        RetrievedPassage(
            chunk_id="p2",
            doc_id="d2",
            filename="B.pdf",
            page_number=1,
            text="Latency was 85ms in benchmark tests.",
        ),
    ]
    res = checker.check("What was the latency?", passages)
    assert res.is_sufficient is True
    assert len(res.contradictions_detected) == 1
    assert "42ms" in res.contradictions_detected[0]

    insuff = checker.check("What was the Kubernetes cluster region?", passages)
    assert insuff.is_sufficient is False
    assert insuff.needs_additional_retrieval is True
    msg = build_missing_evidence_response("What was the Kubernetes cluster region?", insuff.missing_aspects)
    assert "do not contain sufficient evidence" in msg


def test_project_intelligence_and_depth_controls():
    engine = ProjectIntelligenceEngine()
    proj = engine.analyze_project_query("Explain the project for an interview.")
    assert proj.is_project_query is True
    assert proj.project_intent == "interview"
    assert proj.recommended_depth == AnswerDepth.COMPREHENSIVE_PROJECT
    assert "Architecture" in proj.target_sections

    depth = resolve_answer_depth(
        requested_depth=None,
        is_project_query=proj.is_project_query,
        recommended_depth=proj.recommended_depth,
    )
    assert depth == AnswerDepth.COMPREHENSIVE_PROJECT

    covered = engine.inspect_section_coverage(proj, PROJECT_CORPUS)
    assert "Architecture" in covered.documented_sections_found
    assert "Technologies" in covered.documented_sections_found


def test_multi_turn_project_conversation_context():
    rewriter = ConversationQueryRewriter()
    history = [
        {"sender": "user", "text": "Explain the architecture."},
        {"sender": "assistant", "text": "The system uses PostgreSQL and ChromaDB."},
        {"sender": "user", "text": "What database is used?"},
        {"sender": "assistant", "text": "PostgreSQL is used for relational metadata."},
    ]
    resolved = rewriter.resolve_locally("Why was it selected?", chat_history=history)
    assert "PostgreSQL" in resolved
    assert "Explain the architecture" in resolved


def test_claim_level_verification_and_completeness():
    passages = [p for p in PROJECT_CORPUS if p.doc_id == "doc_proj"]
    verifier = ClaimLevelVerifier()

    ans = (
        "DocNest uses FastAPI on the backend and PostgreSQL for relational metadata [DocNest_Project_Report.pdf, p. 3]. "
        "It achieved 0.99 Recall@5 in benchmark tests [DocNest_Project_Report.pdf, p. 5]. "
        "The team deployed it on AWS Lambda."
    )
    items = verifier.verify_answer(ans, passages)
    statuses = [i.status for i in items]
    assert ClaimStatus.SUPPORTED in statuses
    assert ClaimStatus.CONTRADICTED in statuses  # 0.99 vs 0.89
    assert ClaimStatus.UNSUPPORTED in statuses  # AWS Lambda not in corpus

    sanitized, _ = verifier.filter_or_qualify_claims(items, remove_unsupported=True)
    assert "AWS Lambda" not in sanitized
    assert "FastAPI" in sanitized

    comp = AnswerCompletenessChecker().evaluate(ans, ["Results", "Architecture"])
    assert comp.completeness_score == 0.5
    assert "Results" in comp.covered_sections
    assert "Architecture" in comp.missing_documented_sections


@pytest.mark.asyncio
async def test_multi_stage_pipeline_and_100_question_benchmark():
    mem_adapter = _InMemoryCorpusAdapter(corpus=PROJECT_CORPUS)
    flags = FeatureFlagManager(
        overrides={
            "ENABLE_EVIDENCE_GROUNDING": True,
            "ENABLE_PROJECT_INTELLIGENCE": True,
            "ENABLE_CLAIM_VERIFICATION": True,
        }
    )
    pipeline = MultiStagePipeline(
        flags=flags,
        retrieval_engine=HybridRetrievalEngine(base_adapter=mem_adapter),
    )

    async def gen_fn(u_p: str, s_p: str) -> str:
        return "The architecture uses React 18, FastAPI, PostgreSQL, ChromaDB, and Ollama Llama 3.2 [DocNest_Project_Report.pdf, p. 3]."

    # Project query succeeds with citations
    res = await pipeline.run("Describe the complete architecture.", generate_fn=gen_fn)
    assert res.depth == AnswerDepth.DETAILED
    assert len(res.citations) >= 1
    assert res.citations[0].is_valid is True

    # Absent question triggers honest limitation without calling generator
    abs_res = await pipeline.run("What is the CEO's personal phone number?", generate_fn=gen_fn)
    assert abs_res.sufficiency.is_sufficient is False
    assert "do not contain sufficient evidence" in abs_res.answer

    # Verify 100-question benchmark dataset & runner
    dataset = build_hallucination_benchmark_dataset()
    assert len(dataset) == 100
    reports = await run_hallucination_benchmark()
    assert len(reports) == 2
    assert reports[1].retrieval_recall >= reports[0].retrieval_recall
