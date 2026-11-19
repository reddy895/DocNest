import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import SummarizeRequest, SummarizeResponse, CompareRequest, CompareResponse
from backend.app.services.research_service import get_research_service

logger = logging.getLogger("docnest.api.research")
router = APIRouter(prefix="/api/research", tags=["Research"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_documents(request: SummarizeRequest):
    """
    Generate grounded research summaries (executive, detailed, key_findings, or terms).
    """
    research_svc = get_research_service()
    try:
        result = await research_svc.summarize_documents(
            doc_ids=request.doc_ids,
            summary_type=request.summary_type,
            model=request.model,
        )
        return SummarizeResponse(**result)
    except Exception as exc:
        logger.error(f"Summarization error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(exc)}",
        )


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(request: CompareRequest):
    """
    Deep multi-document comparative analysis identifying agreements, contradictions, and comparison matrix.
    """
    if len(request.doc_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two document IDs must be provided for comparative analysis.",
        )
    research_svc = get_research_service()
    try:
        result = await research_svc.compare_documents(
            doc_ids=request.doc_ids,
            comparison_aspects=request.comparison_aspects,
            model=request.model,
        )
        return CompareResponse(**result)
    except Exception as exc:
        logger.error(f"Comparative analysis error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute comparative analysis: {str(exc)}",
        )
