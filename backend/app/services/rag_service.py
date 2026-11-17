import time
import logging
from typing import Optional, List
from backend.app.services.chroma_service import get_chroma_service
from backend.app.services.ollama_service import get_ollama_service
from backend.app.models.schemas import ChatQueryResponse, Citation
from backend.app.core.config import settings

logger = logging.getLogger("docnest.rag")

SYSTEM_GROUNDING_PROMPT = """You are DocNest, a high-precision document intelligence assistant.
Your absolute duty is to provide strictly factual answers grounded ONLY in the retrieved document context below.

STRICT GROUNDING RULES:
1. Answer the question using ONLY the facts explicitly stated in the CONTEXT.
2. If the answer is NOT mentioned or cannot be directly proven by the context, state honestly:
   "I couldn't find this information in the uploaded document(s)."
3. NEVER invent facts, statistics, dates, names, or page numbers.
4. Do NOT use outside knowledge or unverified assumptions.
5. In your answer, clearly cite the supporting sources using the format: [Source X: filename (Page Y)].
6. Keep your answer clear, direct, and professional."""


def format_rag_prompt(question: str, citations: List[Citation]) -> str:
    """
    Assemble structured prompt containing numbered context passages and citation identifiers.
    """
    context_blocks = []
    for idx, c in enumerate(citations):
        source_label = f"Source {idx + 1}: {c.filename} (Page {c.page_number})"
        context_blocks.append(f"[{source_label}]\n{c.content}\n")

    context_str = "\n".join(context_blocks)

    return f"""CONTEXT:
{context_str}

USER QUESTION:
{question}

INSTRUCTIONS:
Provide a concise, grounded answer based strictly on the context above. Include source citations [Source X: filename (Page Y)] directly in your response. If the information is not in the context, say you could not find it.

ANSWER:"""


class RAGService:
    """
    Retrieval-Augmented Generation engine coordinating vector retrieval,
    relevance filtering, prompt grounding, and Ollama inference.
    """

    def __init__(self):
        self.chroma = get_chroma_service()
        self.ollama = get_ollama_service()

    async def answer_question(
        self,
        question: str,
        doc_id: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> ChatQueryResponse:
        start_time = time.time()
        effective_k = top_k or settings.RETRIEVAL_TOP_K
        effective_thresh = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD

        # 1. Retrieve relevant passages
        citations = self.chroma.get_relevant_chunks(
            query_text=question,
            top_k=effective_k,
            doc_id=doc_id,
            similarity_threshold=effective_thresh,
        )

        total_found = len(citations)
        active_model = await self.ollama.get_active_model()

        # 2. Handle zero retrieved context
        if total_found == 0:
            elapsed = time.time() - start_time
            return ChatQueryResponse(
                question=question,
                answer="I couldn't find any relevant information in the uploaded document(s) matching your question. Please ensure the relevant document is uploaded or try rephrasing.",
                citations=[],
                total_sources_found=0,
                is_grounded=False,
                processing_time_seconds=round(elapsed, 3),
                model_used=active_model,
                doc_id_filtered=doc_id,
            )

        # 3. Build grounded prompt and query Ollama
        prompt = format_rag_prompt(question, citations)
        answer = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt=SYSTEM_GROUNDING_PROMPT,
            model=active_model,
            temperature=0.1,  # Strict factual precision
        )

        elapsed = time.time() - start_time

        return ChatQueryResponse(
            question=question,
            answer=answer,
            citations=citations,
            total_sources_found=total_found,
            is_grounded=True,
            processing_time_seconds=round(elapsed, 3),
            model_used=active_model,
            doc_id_filtered=doc_id,
        )


# Global Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

