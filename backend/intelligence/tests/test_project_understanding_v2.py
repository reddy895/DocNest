"""Tests for Phase 7 Deep Project Understanding mode & orchestrator integration."""

from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.evaluation.runner import _InMemoryCorpusAdapter
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.intelligence.project_intelligence.engine import ProjectIntelligenceEngine


def test_project_understanding_flag_defaults_false():
    flags = FeatureFlagManager().get_flags()
    assert flags.ENABLE_PROJECT_UNDERSTANDING is False


def test_orchestrator_project_understanding_retrieves_multi_section_context():
    corpus = [
        RetrievedPassage(
            chunk_id="proj_abs",
            doc_id="d_proj",
            filename="DocNest_Project.pdf",
            page_number=1,
            section_heading="Abstract",
            text="Abstract: DocNest is a local-first RAG project for document intelligence.",
        ),
        RetrievedPassage(
            chunk_id="proj_arch",
            doc_id="d_proj",
            filename="DocNest_Project.pdf",
            page_number=3,
            section_heading="Architecture",
            text="Architecture: The project uses FastAPI, ChromaDB dense vectors, BM25 sparse search, and Ollama.",
        ),
        RetrievedPassage(
            chunk_id="proj_res",
            doc_id="d_proj",
            filename="DocNest_Project.pdf",
            page_number=7,
            section_heading="Results",
            text="Results: Project evaluation showed 42ms reranking latency and 100% citation grounding.",
        ),
    ]
    adapter = _InMemoryCorpusAdapter(corpus=corpus)
    flags = FeatureFlagManager(overrides={"ENABLE_PROJECT_UNDERSTANDING": True})
    orch = IntelligenceOrchestrator(
        flag_manager=flags,
        retriever_adapter=adapter,  # type: ignore[arg-type]
        project_engine=ProjectIntelligenceEngine(),
    )

    _, opt_ctx, trace = orch.prepare_retrieval_and_context(
        question="Explain this entire project in detail.",
        top_k=5,
    )
    assert trace.project_analysis is not None
    assert trace.project_analysis.is_project_query is True
    assert len(trace.project_analysis.target_sections) >= 4
    retrieved_ids = {p.chunk_id for p in opt_ctx.passages}
    assert "proj_arch" in retrieved_ids
    assert len(retrieved_ids) >= 2
