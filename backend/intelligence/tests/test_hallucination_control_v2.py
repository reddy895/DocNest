"""Tests for Phase 8 Hallucination Control: evidence sufficiency, bounded retry, and answer depth."""

from backend.intelligence.answer_verification.evidence_grounding import EvidenceSufficiencyChecker
from backend.intelligence.contracts import AnswerDepth, RetrievedPassage
from backend.intelligence.evaluation.runner import _InMemoryCorpusAdapter
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.intelligence.project_intelligence.engine import ProjectIntelligenceEngine
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine


def test_hallucination_control_flag_defaults_false():
    flags = FeatureFlagManager().get_flags()
    assert flags.ENABLE_HALLUCINATION_CONTROL is False


def test_missing_information_triggers_insufficient_evidence():
    adapter = _InMemoryCorpusAdapter()
    flags = FeatureFlagManager(overrides={"ENABLE_HALLUCINATION_CONTROL": True})
    orch = IntelligenceOrchestrator(
        flag_manager=flags,
        retriever_adapter=adapter,  # type: ignore[arg-type]
        sufficiency_checker=EvidenceSufficiencyChecker(),
    )
    _, _, trace = orch.prepare_retrieval_and_context(
        question="What accuracy did this project achieve on SQuAD v2?",
        top_k=5,
    )
    assert trace.evidence_sufficiency is not None
    assert trace.evidence_sufficiency.is_sufficient is False


def test_contradictory_passages_detected():
    checker = EvidenceSufficiencyChecker()
    p1 = RetrievedPassage(
        chunk_id="a1",
        doc_id="d1",
        filename="Doc1.pdf",
        page_number=1,
        text="Model accuracy was 84.5% in the initial benchmark.",
    )
    p2 = RetrievedPassage(
        chunk_id="a2",
        doc_id="d2",
        filename="Doc2.pdf",
        page_number=2,
        text="Model accuracy was 91.2% in the updated benchmark.",
    )
    res = checker.check("What was the model accuracy?", [p1, p2])
    assert len(res.contradictions_detected) >= 1


def test_answer_depth_prefers_detailed_for_project_and_brief_for_factual():
    adapter = _InMemoryCorpusAdapter()
    flags = FeatureFlagManager(
        overrides={
            "ENABLE_QUERY_INTELLIGENCE": True,
            "ENABLE_PROJECT_UNDERSTANDING": True,
            "ENABLE_HALLUCINATION_CONTROL": True,
        }
    )
    orch = IntelligenceOrchestrator(
        flag_manager=flags,
        retriever_adapter=adapter,  # type: ignore[arg-type]
        query_engine=QueryIntelligenceEngine(),
        project_engine=ProjectIntelligenceEngine(),
        sufficiency_checker=EvidenceSufficiencyChecker(),
    )

    _, _, trace_simple = orch.prepare_retrieval_and_context("What was Q3 revenue?")
    _, _, trace_project = orch.prepare_retrieval_and_context("Explain this entire project in detail.")

    assert trace_simple.recommended_depth in {AnswerDepth.BRIEF, AnswerDepth.NORMAL}
    assert trace_project.recommended_depth in {AnswerDepth.DETAILED, AnswerDepth.COMPREHENSIVE_PROJECT}
