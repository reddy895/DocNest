"""Core domain contracts, typed DTOs, and fallback exceptions for DocNest Intelligence 2.0."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntelligenceFallbackError(Exception):
    """Raised when an enhancement stage fails and should fall back to baseline."""


class QueryIntent(str, Enum):
    FACTUAL = "factual"
    TECHNICAL = "technical"
    COMPARATIVE = "comparative"
    METHODOLOGY = "methodology"
    NUMERICAL = "numerical"
    FOLLOW_UP = "follow_up"
    SUMMARIZATION = "summarization"
    CONVERSATIONAL = "conversational"
    UNANSWERABLE = "unanswerable"


class AnswerStyle(str, Enum):
    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    RESEARCH = "research"
    BEGINNER = "beginner"


class AnswerDepth(str, Enum):
    BRIEF = "brief"
    NORMAL = "normal"
    DETAILED = "detailed"
    COMPREHENSIVE_PROJECT = "comprehensive_project"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


class ClaimVerificationItem(BaseModel):
    claim: str
    status: ClaimStatus
    evidence_score: float = 0.0
    supporting_chunk_id: Optional[str] = None
    reason: Optional[str] = None


class EvidenceSufficiencyResult(BaseModel):
    is_sufficient: bool = True
    coverage_score: float = 1.0
    missing_aspects: List[str] = Field(default_factory=list)
    contradictions_detected: List[str] = Field(default_factory=list)
    needs_additional_retrieval: bool = False


class CompletenessReport(BaseModel):
    is_complete: bool = True
    completeness_score: float = 1.0
    covered_sections: List[str] = Field(default_factory=list)
    missing_documented_sections: List[str] = Field(default_factory=list)


class QueryAnalysis(BaseModel):
    original_query: str
    resolved_query: str
    intent: QueryIntent = QueryIntent.FACTUAL
    expanded_terms: List[str] = Field(default_factory=list)
    sub_queries: List[str] = Field(default_factory=list)
    is_multi_document: bool = False
    is_follow_up: bool = False
    needs_rewriting: bool = False
    referenced_docs: List[str] = Field(default_factory=list)
    language: str = "en"
    confidence: float = 1.0


class RetrievedPassage(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int = 1
    chunk_index: int = 0
    text: str
    section_heading: Optional[str] = None
    workspace_id: str = "Default Workspace"
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    rrf_score: float = 0.0
    rerank_score: Optional[float] = None
    final_score: float = 0.0
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OptimizedContext(BaseModel):
    passages: List[RetrievedPassage] = Field(default_factory=list)
    formatted_context: str = ""
    total_tokens_estimated: int = 0
    token_budget: int = 3000
    deduplicated_count: int = 0
    dropped_count: int = 0
    style: AnswerStyle = AnswerStyle.DETAILED


class VerifiedCitation(BaseModel):
    doc_id: Optional[str] = None
    filename: str
    page_number: int
    chunk_id: Optional[str] = None
    is_valid: bool = False
    alignment_score: float = 0.0
    reason: Optional[str] = None


class AnswerVerificationResult(BaseModel):
    is_faithful: bool = True
    relevance_score: float = 1.0
    faithfulness_score: float = 1.0
    unsupported_claims: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    needs_retry: bool = False
    abstained: bool = False
    notes: List[str] = Field(default_factory=list)


class IntelligenceTrace(BaseModel):
    flags_active: Dict[str, bool] = Field(default_factory=dict)
    query_analysis: Optional[QueryAnalysis] = None
    retrieval_count: int = 0
    reranked_count: int = 0
    context_tokens: int = 0
    citation_verification: List[VerifiedCitation] = Field(default_factory=list)
    answer_verification: Optional[AnswerVerificationResult] = None
    fallback_triggered: bool = False
    fallback_reasons: List[str] = Field(default_factory=list)
    timings_ms: Dict[str, float] = Field(default_factory=dict)

