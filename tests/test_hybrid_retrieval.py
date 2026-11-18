import pytest
from backend.app.services.retrieval_service import (
    reciprocal_rank_fusion,
    RetrievalCandidate,
)
from backend.app.services.reranker_service import sigmoid


def test_reciprocal_rank_fusion_logic():
    # Dense: doc1 (rank 1), doc2 (rank 2)
    dense_results = [
        {"chunk_id": "c1", "doc_id": "d1", "filename": "doc1.pdf", "page_number": 1, "chunk_index": 0, "text": "AI architectures", "score": 0.85},
        {"chunk_id": "c2", "doc_id": "d1", "filename": "doc1.pdf", "page_number": 2, "chunk_index": 1, "text": "BM25 keyword search", "score": 0.70},
    ]
    # Sparse: doc2 (rank 1), doc3 (rank 2)
    sparse_results = [
        ("c2", 4.5),
        ("c3", 3.2),
    ]

    fused = reciprocal_rank_fusion(dense_results, sparse_results, k_constant=60, top_n=5)
    assert len(fused) >= 2

    # c2 was present in BOTH dense (rank 2) and sparse (rank 1)
    # score(c2) = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.016129 + 0.016393 = ~0.03252
    # score(c1) = 1/(60+1) = 1/61 = ~0.01639
    # c2 must rank higher than c1 due to reciprocal rank fusion!
    assert fused[0].chunk_id == "c2"
    assert fused[0].rrf_score > fused[1].rrf_score


def test_sigmoid_normalization():
    # Sigmoid should map 0.0 -> 0.5
    s0 = sigmoid(0.0)
    assert abs(s0 - 0.5) < 1e-5

    # Positive logit -> score > 0.5
    assert sigmoid(2.0) > 0.85

    # Negative logit -> score < 0.5
    assert sigmoid(-2.0) < 0.15


@pytest.mark.asyncio
async def test_abstention_guardrail_behavior():
    from backend.app.services.rag_service import RAGService
    rag = RAGService()

    # Query with impossible terms and a high minimum relevance score threshold
    res = await rag.answer_question(
        question="What is the quantum hyperdrive warp velocity in DocNest?",
        top_k=3,
        min_relevance_score=0.99,  # High threshold guarantees abstention
    )

    assert res.is_grounded is False
    assert res.total_sources_found == 0
    assert "could not find sufficient evidence" in res.answer or "below" in res.answer
