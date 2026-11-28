"""Phase 10 & 11 End-to-End Regression, Feature Flag Isolation, and Fallback Tests."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.intelligence.answer_verification.evidence_grounding import EvidenceSufficiencyChecker
from backend.intelligence.citation_verification.verifier import CitationVerifier
from backend.intelligence.context_optimizer.engine import ContextOptimizationEngine
from backend.intelligence.evaluation.baseline_20q import Baseline20QBenchmarkRunner
from backend.intelligence.evaluation.runner import _InMemoryCorpusAdapter
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.hybrid_retrieval.engine import HybridRetrievalEngine
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.intelligence.project_intelligence.engine import ProjectIntelligenceEngine
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine
from backend.intelligence.reranking.engine import RerankingEngine


PHASE_11_FLAGS = (
    "ENABLE_QUERY_INTELLIGENCE",
    "ENABLE_HYBRID_SEARCH",
    "ENABLE_RERANKING",
    "ENABLE_PROJECT_UNDERSTANDING",
    "ENABLE_HALLUCINATION_CONTROL",
    "ENABLE_CITATION_VERIFICATION",
)


def test_all_phase_11_flags_disabled_by_default():
    flags = FeatureFlagManager().as_dict()
    for flag_name in PHASE_11_FLAGS:
        assert flags[flag_name] is False


@pytest.mark.parametrize("flag_name", PHASE_11_FLAGS)
def test_each_enhancement_can_be_toggled_independently(flag_name):
    adapter = _InMemoryCorpusAdapter()
    flags = FeatureFlagManager(overrides={flag_name: True})
    orch = IntelligenceOrchestrator(
        flag_manager=flags,
        retriever_adapter=adapter,  # type: ignore[arg-type]
        query_engine=QueryIntelligenceEngine(),
        hybrid_engine=HybridRetrievalEngine(base_adapter=adapter),  # type: ignore[arg-type]
        reranking_engine=RerankingEngine(use_cross_encoder=False),
        project_engine=ProjectIntelligenceEngine(),
        context_engine=ContextOptimizationEngine(),
        citation_verifier=CitationVerifier(),
        sufficiency_checker=EvidenceSufficiencyChecker(),
    )
    qa, opt_ctx, trace = orch.prepare_retrieval_and_context(
        question="Explain the hybrid retrieval architecture in this project.",
        top_k=5,
        min_score=0.15,
    )
    assert qa.original_query == "Explain the hybrid retrieval architecture in this project."
    assert trace.flags_active[flag_name] is True
    assert trace.fallback_triggered is False
    assert len(opt_ctx.passages) >= 1


def test_orchestrator_falls_back_gracefully_when_engines_fail():
    class ExplodingEngine:
        def __getattr__(self, _name):
            def _boom(*args, **kwargs):
                raise RuntimeError("simulated stage failure")
            return _boom

    adapter = _InMemoryCorpusAdapter()
    flags = FeatureFlagManager(overrides={k: True for k in PHASE_11_FLAGS})
    orch = IntelligenceOrchestrator(
        flag_manager=flags,
        retriever_adapter=adapter,  # type: ignore[arg-type]
        query_engine=ExplodingEngine(),
        hybrid_engine=ExplodingEngine(),
        reranking_engine=ExplodingEngine(),
        project_engine=ExplodingEngine(),
        citation_verifier=ExplodingEngine(),
        sufficiency_checker=ExplodingEngine(),
    )
    qa, opt_ctx, trace = orch.prepare_retrieval_and_context("What was Q3 revenue?", top_k=5)
    assert qa.resolved_query == "What was Q3 revenue?"
    assert len(opt_ctx.passages) >= 1
    assert trace.fallback_triggered is True
    assert len(trace.fallback_reasons) >= 1


def test_enhanced_20q_benchmark_preserves_or_improves_baseline():
    runner = Baseline20QBenchmarkRunner()
    baseline = runner.run(flag_overrides={}, profile_name="baseline")
    enhanced = runner.run(
        flag_overrides={k: True for k in PHASE_11_FLAGS},
        profile_name="enhanced",
    )
    assert enhanced.total_questions == 20
    assert enhanced.mean_recall_at_5 >= baseline.mean_recall_at_5
    assert enhanced.citation_accuracy == 1.0


def test_existing_fastapi_health_endpoint_preserved():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert "status" in payload
