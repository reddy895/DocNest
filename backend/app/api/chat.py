import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import ChatQueryRequest, ChatQueryResponse
from backend.app.services.rag_service import get_rag_service
from backend.app.services.chroma_service import get_chroma_service

logger = logging.getLogger("docnest.api.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])


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
