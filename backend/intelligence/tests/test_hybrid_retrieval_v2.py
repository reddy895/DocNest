"""Tests for Phase 5 Hybrid Retrieval Adapter: weights, page filters, metadata, and fallback."""

from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.hybrid_retrieval.engine import HybridRetrievalEngine


class _StubBaseRetriever:
    def __init__(self, passages):
        self._passages = passages

    def retrieve(self, query, top_k=20, doc_ids=None, workspace_id=None, search_mode="hybrid"):
        return [p.model_copy(deep=True) for p in self._passages][:top_k]


def _make_passages():
    return [
        RetrievedPassage(
            chunk_id="c1",
            doc_id="d1",
            filename="PaperA.pdf",
            page_number=1,
            chunk_index=0,
            section_heading="Overview",
            text="ChromaDB vector search with nomic-embed-text.",
            dense_score=0.80,
            sparse_score=0.50,
            metadata={"source": "unit-test"},
        ),
        RetrievedPassage(
            chunk_id="c2",
            doc_id="d1",
            filename="PaperA.pdf",
            page_number=3,
            chunk_index=2,
            section_heading="Evaluation",
            text="BM25 keyword retrieval achieved 0.85 recall.",
            dense_score=0.40,
            sparse_score=0.90,
            metadata={"source": "unit-test"},
        ),
        RetrievedPassage(
            chunk_id="c1",  # duplicate
            doc_id="d1",
            filename="PaperA.pdf",
            page_number=1,
            chunk_index=0,
            section_heading="Overview",
            text="ChromaDB vector search with nomic-embed-text.",
            dense_score=0.80,
            sparse_score=0.50,
        ),
    ]


def test_hybrid_retrieval_page_filtering_and_deduplication():
    adapter = _StubBaseRetriever(_make_passages())
    engine = HybridRetrievalEngine(base_adapter=adapter)  # type: ignore[arg-type]

    results = engine.retrieve(
        query="BM25 keyword retrieval",
        top_k=5,
        doc_ids=["d1"],
        page_numbers=[3],
        dense_weight=0.4,
        sparse_weight=0.6,
    )
    assert len(results) == 1
    assert results[0].chunk_id == "c2"
    assert results[0].page_number == 3
    assert results[0].metadata.get("source") == "unit-test"


def test_hybrid_retrieval_falls_back_to_base_on_fusion_error():
    class BrokenFusion:
        def fuse(self, *args, **kwargs):
            raise RuntimeError("fusion error")

    adapter = _StubBaseRetriever(_make_passages())
    engine = HybridRetrievalEngine(base_adapter=adapter, fusion=BrokenFusion())  # type: ignore[arg-type]

    results = engine.retrieve(query="ChromaDB", top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
