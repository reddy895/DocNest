import json
import time
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import ChatQueryRequest, ChatQueryResponse, StreamChatRequest, Citation
from backend.app.services.rag_service import get_rag_service, format_grounded_prompt, SYSTEM_GROUNDING_PROMPT
from backend.app.services.retrieval_service import get_retriever
from backend.app.services.reranker_service import get_reranker
from backend.app.services.ollama_service import get_ollama_service
from backend.app.services.chroma_service import get_chroma_service
from backend.app.core.config import settings

logger = logging.getLogger("docnest.api.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/stream")
async def stream_chat(request: StreamChatRequest):
    """
    Real-time Server-Sent Events (SSE) streaming endpoint yielding:
    - Status milestones (rewriting -> hybrid retrieval -> reranking)
    - Retrieval citations & latency traces
    - Token-by-token generation from Ollama Llama 3.2
    - Inline citations and completion event
    """
    async def sse_event_generator() -> AsyncGenerator[str, None]:
        start_time = time.time()
        ollama = get_ollama_service()
        retriever = get_retriever()
        reranker = get_reranker()

        trace: Dict[str, Any] = {}
        target_docs = request.doc_ids
        effective_k = request.top_k or 5
        min_score = request.min_relevance_score if request.min_relevance_score is not None else 0.30

        # Step 1: Rewriting
        yield f"data: {json.dumps({'event': 'status', 'stage': 'rewriting', 'message': 'Resolving context & query...'})}\n\n"
        t0 = time.time()
        rewritten_query = request.question
        if request.chat_history:
            rewritten_query = await ollama.rewrite_conversational_query(request.question, request.chat_history)
        trace["query_rewriting_ms"] = round((time.time() - t0) * 1000, 2)
        trace["rewritten_query"] = rewritten_query

        # Step 2: Hybrid Retrieval
        yield f"data: {json.dumps({'event': 'status', 'stage': 'retrieving', 'message': 'Executing dense vector + BM25 sparse search...'})}\n\n"
        t1 = time.time()
        candidates = retriever.retrieve(query=rewritten_query, top_k=20, doc_ids=target_docs)
        trace["retrieval_ms"] = round((time.time() - t1) * 1000, 2)
        trace["candidate_count"] = len(candidates)

        # Step 3: Cross-Encoder Reranking
        yield f"data: {json.dumps({'event': 'status', 'stage': 'reranking', 'message': 'Cross-Encoder evaluating relevance scores...'})}\n\n"
        t2 = time.time()
        reranked = reranker.rerank(query=rewritten_query, candidates=candidates, top_k=effective_k, min_relevance_score=min_score)
        trace["rerank_ms"] = round((time.time() - t2) * 1000, 2)
        trace["reranked_count"] = len(reranked)

        max_score = max([c.reranker_score or 0.0 for c in candidates]) if candidates else 0.0
        trace["max_relevance_score"] = round(max_score, 4)

        # Step 4: Emit Retrieval Metadata
        citation_payloads = [
            {
                "source_id": c.chunk_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "content": c.text,
                "relevance_score": c.reranker_score or 0.5,
                "section_heading": c.section_heading,
                "dense_rank": c.dense_rank,
                "sparse_rank": c.sparse_rank,
                "rrf_score": round(c.rrf_score, 4),
            }
            for c in reranked
        ]
        yield f"data: {json.dumps({'event': 'retrieval', 'citations': citation_payloads, 'trace': trace})}\n\n"

        # Check Abstention Guardrail
        if not reranked or max_score < min_score:
            abstention_text = (
                f"I could not find sufficient evidence in the uploaded documents to answer this question. "
                f"The highest relevance score for your query was {max_score:.2f}, which is below "
                f"our confidence threshold of {min_score:.2f}."
            )
            for word in abstention_text.split(" "):
                yield f"data: {json.dumps({'event': 'token', 'token': word + ' '})}\n\n"
            trace["total_ms"] = round((time.time() - start_time) * 1000, 2)
            yield f"data: {json.dumps({'event': 'done', 'full_text': abstention_text, 'is_grounded': False, 'trace': trace})}\n\n"
            return

        # Step 5: LLM Generation Streaming
        yield f"data: {json.dumps({'event': 'status', 'stage': 'generating', 'message': 'Generating grounded response...'})}\n\n"
        prompt = format_grounded_prompt(rewritten_query, reranked)
        active_model = await ollama.get_active_model()

        accumulated_text = []
        token_count = 0
        t3 = time.time()
        ttft_recorded = False

        async for token in ollama.stream_response(
            prompt=prompt,
            system_prompt=SYSTEM_GROUNDING_PROMPT,
            model=active_model,
            temperature=request.temperature or 0.1,
        ):
            if not ttft_recorded:
                trace["ttft_ms"] = round((time.time() - t3) * 1000, 2)
                ttft_recorded = True
            token_count += 1
            accumulated_text.append(token)
            yield f"data: {json.dumps({'event': 'token', 'token': token})}\n\n"

        trace["generation_ms"] = round((time.time() - t3) * 1000, 2)
        trace["total_ms"] = round((time.time() - start_time) * 1000, 2)
        full_text = "".join(accumulated_text)

        yield f"data: {json.dumps({'event': 'done', 'full_text': full_text, 'is_grounded': True, 'tokens': token_count, 'trace': trace})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")


@router.post("/query", response_model=ChatQueryResponse)
async def query_chat(request: ChatQueryRequest):
    """
    Submit a natural language question. Retrieves relevant PDF chunks from ChromaDB,
    constructs a strictly grounded prompt, and queries local Llama 3.2 via Ollama.
    """
    rag = get_rag_service()
    try:
        response = await rag.answer_question(
            question=request.question,
            doc_id=request.doc_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )
        return response
    except Exception as exc:
        logger.error(f"Chat query execution failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(exc)}",
        )


@router.get("/suggestions")
async def get_suggested_questions(doc_id: Optional[str] = None):
    """
    Provide dynamic question suggestions for the user interface.
    """
    chroma = get_chroma_service()

    if doc_id:
        doc = chroma.find_document_by_id(doc_id)
        doc_name = doc.filename if doc else "this document"
        return {
            "doc_id": doc_id,
            "suggestions": [
                f"What is the executive summary of {doc_name}?",
                f"What are the key conclusions or findings in {doc_name}?",
                f"What dates, deadlines, or milestones are mentioned in {doc_name}?",
                f"Can you list the main metrics or statistics in {doc_name}?",
            ],
        }

    # Global repository suggestions
    total_docs = len(chroma.list_documents())
    if total_docs == 0:
        return {
            "doc_id": None,
            "suggestions": [
                "Upload a PDF document to begin asking questions.",
            ],
        }

    return {
        "doc_id": None,
        "suggestions": [
            "What are the main topics discussed across the uploaded documents?",
            "Can you summarize the most important findings?",
            "What specific numbers, budgets, or dates are mentioned?",
            "What recommendations or action items are outlined?",
        ],
    }

