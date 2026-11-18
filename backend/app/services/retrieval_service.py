import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.chroma_service import get_chroma_service
from backend.app.services.bm25_service import get_bm25_service

logger = logging.getLogger("docnest.retrieval")


class RetrievalCandidate(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    section_heading: Optional[str] = None
    workspace_id: str = "Default Workspace"
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    rrf_score: float = 0.0
    reranker_score: Optional[float] = None

    @property
    def source(self) -> str:
        return f"{self.filename} (Page {self.page_number})"


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[tuple[str, float]],
    k_constant: int = 60,
    top_n: int = 20,
) -> List[RetrievalCandidate]:
    """
    Combine dense vector candidates and BM25 sparse candidates using
    Reciprocal Rank Fusion (RRF): RRF(d) = sum(1 / (k + rank)).
    """
    fused_scores: Dict[str, float] = {}
    dense_ranks: Dict[str, int] = {}
    dense_scores_map: Dict[str, float] = {}
    sparse_ranks: Dict[str, int] = {}
    sparse_scores_map: Dict[str, float] = {}
    candidate_data: Dict[str, Dict[str, Any]] = {}

    # 1. Process dense vector candidates
    for rank, item in enumerate(dense_results, start=1):
        cid = item["chunk_id"]
        dense_ranks[cid] = rank
        dense_scores_map[cid] = item.get("score", 0.0)
        fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (k_constant + rank))
        candidate_data[cid] = item

    # 2. Process sparse BM25 candidates
    bm25_svc = get_bm25_service()
    for rank, (cid, s_score) in enumerate(sparse_results, start=1):
        sparse_ranks[cid] = rank
        sparse_scores_map[cid] = s_score
        fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (k_constant + rank))

        if cid not in candidate_data and cid in bm25_svc.corpus:
            info = bm25_svc.corpus[cid]
            candidate_data[cid] = {
                "chunk_id": cid,
                "doc_id": info["doc_id"],
                "filename": info["filename"],
                "page_number": info["page_number"],
                "chunk_index": info["chunk_index"],
                "text": info["text"],
                "section_heading": info.get("section_heading"),
                "workspace_id": info.get("workspace_id", "Default Workspace"),
            }

    # 3. Sort by fused RRF score
    sorted_cids = sorted(fused_scores.keys(), key=lambda c: fused_scores[c], reverse=True)[:top_n]

    candidates: List[RetrievalCandidate] = []
    for cid in sorted_cids:
        data = candidate_data.get(cid)
        if not data:
            continue
        candidates.append(
            RetrievalCandidate(
                chunk_id=cid,
                doc_id=data.get("doc_id", ""),
                filename=data.get("filename", ""),
                page_number=data.get("page_number", 1),
                chunk_index=data.get("chunk_index", 0),
                text=data.get("text", ""),
                section_heading=data.get("section_heading"),
                workspace_id=data.get("workspace_id", "Default Workspace"),
                dense_rank=dense_ranks.get(cid),
                sparse_rank=sparse_ranks.get(cid),
                dense_score=dense_scores_map.get(cid),
                sparse_score=sparse_scores_map.get(cid),
                rrf_score=fused_scores[cid],
            )
        )

    return candidates


class HybridRetriever:
    """
    Executes dense semantic retrieval + BM25 sparse keyword retrieval,
    fusing results with Reciprocal Rank Fusion.
    """

    def __init__(self):
        self.chroma = get_chroma_service()
        self.bm25 = get_bm25_service()

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        dense_limit: int = 20,
        sparse_limit: int = 20,
    ) -> List[RetrievalCandidate]:
        """
        Query ChromaDB and BM25 concurrently and fuse ranks with RRF.
        """
        # 1. Query Dense ChromaDB
        where_filter: Optional[Dict[str, Any]] = None
        if doc_ids and len(doc_ids) == 1:
            where_filter = {"doc_id": doc_ids[0]}
        elif doc_ids and len(doc_ids) > 1:
            where_filter = {"doc_id": {"$in": doc_ids}}

        dense_raw = self.chroma.query_collection(
            query_text=query,
            n_results=dense_limit,
            where_filter=where_filter,
        )

        dense_candidates: List[Dict[str, Any]] = []
        for match in dense_raw:
            dense_candidates.append({
                "chunk_id": match.chunk_id,
                "doc_id": match.doc_id,
                "filename": match.filename,
                "page_number": match.page_number,
                "chunk_index": match.chunk_index,
                "text": match.text,
                "score": match.similarity_score,
                "section_heading": match.metadata.section_heading if hasattr(match.metadata, "section_heading") else None,
                "workspace_id": match.metadata.workspace_id if hasattr(match.metadata, "workspace_id") else "Default Workspace",
            })

        # 2. Query Sparse BM25
        sparse_results = self.bm25.search(
            query=query,
            top_k=sparse_limit,
            doc_ids=doc_ids,
            workspace_id=workspace_id,
        )

        # 3. Reciprocal Rank Fusion
        return reciprocal_rank_fusion(
            dense_results=dense_candidates,
            sparse_results=sparse_results,
            k_constant=60,
            top_n=top_k,
        )


_retriever_instance: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
