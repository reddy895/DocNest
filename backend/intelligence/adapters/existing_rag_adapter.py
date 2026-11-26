"""Read-only adapter wrapping existing DocNest retrieval, reranker, and Ollama services."""

from typing import List, Optional
from backend.app.services.retrieval_service import get_retriever, RetrievalCandidate
from backend.app.services.reranker_service import get_reranker
from backend.app.services.ollama_service import get_ollama_service
from backend.intelligence.contracts import RetrievedPassage


def candidate_to_passage(candidate: RetrievalCandidate) -> RetrievedPassage:
    """Convert existing RetrievalCandidate into an Intelligence RetrievedPassage."""
    score = candidate.reranker_score if candidate.reranker_score is not None else candidate.rrf_score
    return RetrievedPassage(
        chunk_id=candidate.chunk_id,
        doc_id=candidate.doc_id,
        filename=candidate.filename,
        page_number=candidate.page_number,
        chunk_index=candidate.chunk_index,
        text=candidate.text,
        section_heading=candidate.section_heading,
        workspace_id=candidate.workspace_id,
        dense_score=candidate.dense_score,
        sparse_score=candidate.sparse_score,
        rrf_score=candidate.rrf_score,
        rerank_score=candidate.reranker_score,
        final_score=float(score or 0.0),
        dense_rank=candidate.dense_rank,
        sparse_rank=candidate.sparse_rank,
        metadata={
            "doc_id": candidate.doc_id,
            "filename": candidate.filename,
            "page_number": candidate.page_number,
            "chunk_index": candidate.chunk_index,
            "section_heading": candidate.section_heading,
            "workspace_id": candidate.workspace_id,
        },
    )


def passage_to_candidate(passage: RetrievedPassage) -> RetrievalCandidate:
    """Convert Intelligence RetrievedPassage back to RetrievalCandidate for baseline compatibility."""
    return RetrievalCandidate(
        chunk_id=passage.chunk_id,
        doc_id=passage.doc_id,
        filename=passage.filename,
        page_number=passage.page_number,
        chunk_index=passage.chunk_index,
        text=passage.text,
        section_heading=passage.section_heading,
        workspace_id=passage.workspace_id,
        dense_rank=passage.dense_rank,
        sparse_rank=passage.sparse_rank,
        dense_score=passage.dense_score,
        sparse_score=passage.sparse_score,
        rrf_score=passage.rrf_score,
        reranker_score=passage.rerank_score,
    )


class ExistingRetrieverAdapter:
    """Consumes existing HybridRetriever results without modifying existing services."""

    def __init__(self, retriever=None):
        self._retriever = retriever

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        search_mode: str = "hybrid",
    ) -> List[RetrievedPassage]:
        candidates = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            doc_ids=doc_ids,
            workspace_id=workspace_id,
            search_mode=search_mode,
        )
        return [candidate_to_passage(c) for c in candidates]


class ExistingRerankerAdapter:
    """Wraps existing CrossEncoderReranker."""

    def __init__(self, reranker=None):
        self._reranker = reranker

    @property
    def reranker(self):
        if self._reranker is None:
            self._reranker = get_reranker()
        return self._reranker

    def rerank(
        self,
        query: str,
        passages: List[RetrievedPassage],
        top_k: int = 5,
        min_score: float = 0.30,
    ) -> List[RetrievedPassage]:
        candidates = [passage_to_candidate(p) for p in passages]
        reranked = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
            min_relevance_score=min_score,
        )
        return [candidate_to_passage(c) for c in reranked]


class ExistingOllamaAdapter:
    """Wraps existing OllamaService."""

    def __init__(self, ollama=None):
        self._ollama = ollama

    @property
    def ollama(self):
        if self._ollama is None:
            self._ollama = get_ollama_service()
        return self._ollama

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        return await self.ollama.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
        )
