import time
import logging
from typing import Optional, List, Dict, Any
from backend.app.services.retrieval_service import get_retriever, RetrievalCandidate
from backend.app.services.reranker_service import get_reranker
from backend.app.services.ollama_service import get_ollama_service
from backend.app.models.schemas import ChatQueryResponse, Citation
from backend.app.core.config import settings

logger = logging.getLogger("docnest.rag")

SYSTEM_GROUNDING_PROMPT = """You are DocNest, an enterprise-grade document intelligence assistant.
Your absolute duty is to provide strictly factual, clear answers grounded ONLY in the retrieved document context below.

STRICT GROUNDING & CITATION RULES:
1. Answer the question using ONLY the facts explicitly stated in the CONTEXT.
2. In your answer, cite every single factual claim inline using the exact structured bracket format: [Filename, p. X] (e.g. [Quarterly Report.pdf, p. 3]).
3. If the context does not contain sufficient facts to answer the question, state honestly:
   "I could not find sufficient evidence in the uploaded documents to answer this question."
4. NEVER invent facts, statistics, percentages, dates, names, or page citations.
5. Do NOT use external knowledge or unsupported extrapolation.
6. Keep your answer professional, direct, and well-structured with bullet points where appropriate."""


def format_grounded_prompt(question: str, candidates: List[RetrievalCandidate]) -> str:
    """
    Assemble structured prompt containing attributed context passages.
    """
    context_blocks = []
    for c in candidates:
        heading_part = f" - {c.section_heading}" if c.section_heading else ""
        context_blocks.append(
            f"--- PASSAGE FROM [{c.filename}, p. {c.page_number}{heading_part}] ---\n{c.text}\n"
        )

    context_str = "\n".join(context_blocks)

    return f"""CONTEXT PASSAGES:
{context_str}

USER QUESTION:
{question}

INSTRUCTIONS:
Provide a concise, grounded answer based strictly on the context passages above. Cite every factual claim inline using the exact format [Filename, p. X]. If the context lacks evidence, abstain cleanly.

ANSWER:"""


class RAGService:
    """
    Production RAG pipeline coordinating conversational rewriting,
    dense + sparse hybrid retrieval, Cross-Encoder reranking,
    abstention guardrails, and grounded LLM generation.
    """

    def __init__(self):
        self.retriever = get_retriever()
        self.reranker = get_reranker()
        self.ollama = get_ollama_service()

    async def answer_question(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        top_k: Optional[int] = None,
        min_relevance_score: Optional[float] = None,
        temperature: float = 0.1,
    ) -> ChatQueryResponse:
        start_time = time.time()
        effective_k = top_k or settings.RETRIEVAL_TOP_K
        effective_min_score = (
            min_relevance_score
            if min_relevance_score is not None
            else settings.MIN_RELEVANCE_SCORE
        )

        trace: Dict[str, Any] = {}

        # 1. Conversational Query Rewriting
        t0 = time.time()
        rewritten_query = question
        if chat_history and len(chat_history) > 0:
            rewritten_query = await self.ollama.rewrite_conversational_query(
                query=question, chat_history=chat_history
            )
        trace["query_rewriting_ms"] = round((time.time() - t0) * 1000, 2)
        trace["rewritten_query"] = rewritten_query

        # 2. Hybrid Retrieval (Dense + BM25 + RRF)
        t1 = time.time()
        candidates = self.retriever.retrieve(
            query=rewritten_query,
            top_k=20,
            doc_ids=doc_ids,
            workspace_id=workspace_id,
        )
        trace["retrieval_ms"] = round((time.time() - t1) * 1000, 2)
        trace["retrieved_candidate_count"] = len(candidates)

        # 3. Cross-Encoder Reranking
        t2 = time.time()
        reranked_candidates = self.reranker.rerank(
            query=rewritten_query,
            candidates=candidates,
            top_k=effective_k,
            min_relevance_score=effective_min_score,
        )
        trace["rerank_ms"] = round((time.time() - t2) * 1000, 2)
        trace["reranked_candidate_count"] = len(reranked_candidates)

        max_score = (
            max([c.reranker_score or 0.0 for c in candidates]) if candidates else 0.0
        )
        trace["max_relevance_score"] = round(max_score, 4)

        active_model = await self.ollama.get_active_model()

        # 4. Abstention Guardrail: Check if candidates meet relevance threshold
        if not reranked_candidates or max_score < effective_min_score:
            elapsed = time.time() - start_time
            trace["abstention_triggered"] = True
            trace["total_ms"] = round(elapsed * 1000, 2)

            abstention_msg = (
                f"I could not find sufficient evidence in the uploaded documents to answer this question. "
                f"The highest relevance score for your query was {max_score:.2f}, which is below "
                f"our confidence threshold of {effective_min_score:.2f}."
            )

            return ChatQueryResponse(
                question=question,
                answer=abstention_msg,
                citations=[],
                total_sources_found=0,
                is_grounded=False,
                processing_time_seconds=round(elapsed, 3),
                model_used=active_model,
                doc_id_filtered=doc_ids[0] if (doc_ids and len(doc_ids) == 1) else None,
            )

        # 5. Convert candidates to Citation objects
        citations = [
            Citation(
                source_id=c.chunk_id,
                filename=c.filename,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                content=c.text,
                relevance_score=c.reranker_score or 0.5,
            )
            for c in reranked_candidates
        ]

        # 6. Grounded LLM Generation
        t3 = time.time()
        prompt = format_grounded_prompt(rewritten_query, reranked_candidates)
        answer = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt=SYSTEM_GROUNDING_PROMPT,
            model=active_model,
            temperature=temperature,
        )
        trace["generation_ms"] = round((time.time() - t3) * 1000, 2)

        elapsed = time.time() - start_time
        trace["total_ms"] = round(elapsed * 1000, 2)

        return ChatQueryResponse(
            question=question,
            answer=answer,
            citations=citations,
            total_sources_found=len(citations),
            is_grounded=True,
            processing_time_seconds=round(elapsed, 3),
            model_used=active_model,
            doc_id_filtered=doc_ids[0] if (doc_ids and len(doc_ids) == 1) else None,
        )


# Global Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
