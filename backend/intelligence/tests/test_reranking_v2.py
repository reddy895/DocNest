"""Tests for Phase 6 Reranking Engine: metadata preservation, score integrity, and fallback."""

from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.reranking.engine import RerankingEngine


def _passages():
    return [
        RetrievedPassage(
            chunk_id="c_low",
            doc_id="d1",
            filename="Doc1.pdf",
            page_number=2,
            chunk_index=1,
            text="Unrelated weather forecast and lunch menu notes.",
            metadata={"origin": "test-a"},
        ),
        RetrievedPassage(
            chunk_id="c_high",
            doc_id="d2",
            filename="Doc2.pdf",
            page_number=5,
            chunk_index=3,
            text="Cross-Encoder reranking evaluates top candidates in 42ms CPU latency.",
            metadata={"origin": "test-b"},
        ),
    ]


def test_reranking_preserves_metadata_and_ranks_relevant_first():
    engine = RerankingEngine(use_cross_encoder=False)
    ranked = engine.rerank("Cross-Encoder reranking CPU latency", _passages(), top_k=2, min_score=0.1)
    assert ranked[0].chunk_id == "c_high"
    assert ranked[0].doc_id == "d2"
    assert ranked[0].page_number == 5
    assert ranked[0].filename == "Doc2.pdf"
    assert ranked[0].metadata.get("origin") == "test-b"


def test_reranking_retains_original_order_and_none_score_when_disabled():
    engine = RerankingEngine(use_cross_encoder=False, allow_lexical_fallback=False)
    passages = _passages()
    ranked = engine.rerank("Cross-Encoder", passages, top_k=2)
    assert [p.chunk_id for p in ranked] == ["c_low", "c_high"]
    assert ranked[0].rerank_score is None
    assert ranked[1].rerank_score is None


def test_reranking_falls_back_to_original_order_on_exception():
    class BrokenCrossEncoder:
        def rerank(self, *args, **kwargs):
            raise RuntimeError("model unavailable")

    engine = RerankingEngine(cross_encoder=BrokenCrossEncoder(), use_cross_encoder=True)  # type: ignore[arg-type]
    passages = _passages()
    ranked = engine.rerank("Cross-Encoder", passages, top_k=2)
    assert [p.chunk_id for p in ranked] == ["c_low", "c_high"]
