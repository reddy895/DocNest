"""Unit tests for Feature Flags, Query Intelligence, Hybrid Retrieval, and Reranking."""

import pytest

from backend.intelligence.contracts import QueryIntent, RetrievedPassage
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine
from backend.intelligence.hybrid_retrieval.normalizer import normalize_passages, compute_keyword_score
from backend.intelligence.hybrid_retrieval.filters import MetadataFilterEngine
from backend.intelligence.hybrid_retrieval.fusion import WeightedHybridFusion
from backend.intelligence.hybrid_retrieval.deduplicator import (
    PassageDeduplicator,
    assert_compatible_embedding_dim,
)
from backend.intelligence.reranking.engine import RerankingEngine
from backend.intelligence.reranking.lexical_scorer import LightweightOverlapScorer


def _sample_passages():
    return [
        RetrievedPassage(
            chunk_id="c1",
            doc_id="d1",
            filename="Report.pdf",
            page_number=1,
            chunk_index=0,
            section_heading="Revenue",
            workspace_id="ws1",
            text="Q3 total revenue grew 19.4% to $48.2 million from enterprise subscriptions.",
            dense_score=0.82,
            sparse_score=0.75,
            rrf_score=0.033,
        ),
        RetrievedPassage(
            chunk_id="c2",
            doc_id="d2",
            filename="Architecture.pdf",
            page_number=2,
            chunk_index=1,
            section_heading="RAG Pipeline",
            workspace_id="ws1",
            text="ChromaDB dense vectors and BM25 sparse search combine via Reciprocal Rank Fusion.",
            dense_score=0.41,
            sparse_score=0.35,
            rrf_score=0.020,
        ),
        RetrievedPassage(
            chunk_id="c1",  # duplicate chunk_id
            doc_id="d1",
            filename="Report.pdf",
            page_number=1,
            chunk_index=0,
            workspace_id="ws1",
            text="Q3 total revenue grew 19.4% to $48.2 million from enterprise subscriptions.",
            dense_score=0.80,
            sparse_score=0.70,
            rrf_score=0.030,
        ),
    ]


def test_feature_flags_default_disabled(monkeypatch):
    for name in FeatureFlagManager.FLAG_NAMES:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(f"DOCNEST_{name}", raising=False)

    mgr = FeatureFlagManager()
    flags = mgr.as_dict()
    assert all(v is False for v in flags.values())

    monkeypatch.setenv("DOCNEST_ENABLE_HYBRID_SEARCH", "true")
    assert mgr.is_enabled("ENABLE_HYBRID_SEARCH") is True
    assert mgr.is_enabled("ENABLE_RERANKING") is False


def test_query_intelligence_classification_and_rewriting():
    engine = QueryIntelligenceEngine()

    qa_comp = engine.analyze("Compare Cloud AI and On-Prem margins")
    assert qa_comp.intent == QueryIntent.COMPARATIVE
    assert qa_comp.is_multi_document is True
    assert len(qa_comp.sub_queries) == 2

    qa_follow = engine.analyze(
        "What is its latency?",
        chat_history=[{"sender": "user", "text": "Cross-Encoder reranking"}],
    )
    assert qa_follow.is_follow_up is True
    assert qa_follow.needs_rewriting is True
    assert "Cross-Encoder reranking" in qa_follow.resolved_query

    qa_direct = engine.analyze("What is the RAG latency?")
    assert qa_direct.needs_rewriting is False
    assert qa_direct.resolved_query == "What is the RAG latency?"
    assert "response time" in qa_direct.expanded_terms


def test_hybrid_retrieval_normalization_filters_and_dedup():
    passages = _sample_passages()
    dedup = PassageDeduplicator().deduplicate(passages)
    assert len(dedup) == 2

    normed = normalize_passages(dedup)
    assert normed[0].dense_score == 1.0
    assert normed[1].dense_score == 0.0

    filtered = MetadataFilterEngine.apply_filters(dedup, doc_ids=["d1"], page_numbers=[1])
    assert len(filtered) == 1
    assert filtered[0].doc_id == "d1"

    fused = WeightedHybridFusion().fuse("Q3 revenue enterprise", dedup)
    assert fused[0].chunk_id == "c1"
    assert compute_keyword_score("revenue", dedup[0].text) > 0.0

    with pytest.raises(ValueError):
        assert_compatible_embedding_dim(768, 384)


def test_reranking_engine_and_fallback():
    passages = _sample_passages()[:2]
    scorer = LightweightOverlapScorer()
    scored = scorer.score_batch("Q3 revenue million", passages)
    assert scored[0].chunk_id == "c1"
    assert scored[0].rerank_score is not None

    class FailingCrossEncoder:
        def rerank(self, *args, **kwargs):
            raise RuntimeError("Simulated model failure")

    engine = RerankingEngine(cross_encoder=FailingCrossEncoder(), use_cross_encoder=True)
    # Must fall back gracefully to original passages without raising
    res = engine.rerank("Q3 revenue", passages, top_k=2)
    assert len(res) == 2
    assert res[0].doc_id in {"d1", "d2"}
