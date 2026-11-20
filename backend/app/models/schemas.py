from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of PDF file validation."""
    is_valid: bool
    filename: str
    file_size_bytes: int
    file_hash: str
    error_message: Optional[str] = None
    warning: Optional[str] = None


class DocumentUpdateRequest(BaseModel):
    """Payload to update document metadata and tags."""
    filename: Optional[str] = None
    tags: Optional[List[str]] = None
    workspace_id: Optional[str] = None


class CollectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = ""
    color: Optional[str] = "#E5B83D"
    document_ids: List[str] = Field(default_factory=list)


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    document_ids: Optional[List[str]] = None


class CollectionInfo(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    name: str
    description: str
    color: str
    document_ids: List[str]
    document_count: int
    created_at: str
    updated_at: str


class DocumentInfo(BaseModel):
    """Metadata for an uploaded document."""
    doc_id: str
    user_id: str = "user_default_local"
    workspace_id: str = "Default Workspace"
    filename: str
    file_size_bytes: int
    file_hash: str
    page_count: int
    total_chunks: int
    upload_date: str
    status: str = "ready"
    progress_pct: int = 100
    error_msg: Optional[str] = None
    is_scanned: bool = False
    tags: List[str] = Field(default_factory=list)


class DocumentStatusResponse(BaseModel):
    """Real-time processing status of an ingestion job."""
    doc_id: str
    filename: str
    status: str
    progress_pct: int
    error_msg: Optional[str] = None
    page_count: int
    total_chunks: int
    is_scanned: bool
    updated_at: str


class DocumentListResponse(BaseModel):
    """Response containing list of documents and summary statistics."""
    total_documents: int
    total_chunks: int
    documents: List[DocumentInfo]


class DeleteDocumentResponse(BaseModel):
    """Response after deleting a document."""
    doc_id: str
    filename: str
    chunks_deleted: int
    success: bool
    message: str


class Citation(BaseModel):
    """Document citation supporting an AI answer."""
    source_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Conversation"


class ChatSessionInfo(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    title: str
    is_pinned: bool = False
    created_at: str
    updated_at: str
    message_count: int = 0


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


class ChatMessageInfo(BaseModel):
    id: str
    session_id: str
    user_id: str
    sender: str
    text: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_trace: Dict[str, Any] = Field(default_factory=dict)
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None
    created_at: str


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=-1, le=1)  # 1 for up, -1 for down, 0 for neutral
    comment: Optional[str] = None


class ChatQueryRequest(BaseModel):
    """Incoming user question request."""
    question: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
    doc_id: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=12)
    min_relevance_score: Optional[float] = Field(default=0.30, ge=0.0, le=1.0)
    similarity_threshold: Optional[float] = Field(default=0.25, ge=0.0, le=1.0)
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=1.0)


class StreamChatRequest(BaseModel):
    """Payload for real-time SSE token streaming."""
    question: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=12)
    min_relevance_score: Optional[float] = Field(default=0.30, ge=0.0, le=1.0)
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=1.0)
    model: Optional[str] = None


class ChatQueryResponse(BaseModel):
    """Generated grounded answer with source citations."""
    question: str
    answer: str
    citations: List[Citation]
    total_sources_found: int
    is_grounded: bool
    processing_time_seconds: float
    model_used: str
    doc_id_filtered: Optional[str] = None


# --- Phase 4: Research Studio Schemas ---

class SummarizeRequest(BaseModel):
    doc_ids: Optional[List[str]] = None
    summary_type: str = Field(default="executive", description="executive, detailed, key_findings, or terms")
    model: Optional[str] = None


class SummarizeResponse(BaseModel):
    summary_type: str
    content: str
    sources_used: int
    processing_time_seconds: float
    model_used: str


class CompareRequest(BaseModel):
    doc_ids: List[str] = Field(min_length=2, description="At least two document IDs to compare")
    comparison_aspects: Optional[List[str]] = None
    model: Optional[str] = None


class CompareResponse(BaseModel):
    documents_compared: List[str]
    overview: str
    agreements: List[str]
    contradictions: List[str]
    matrix: str
    processing_time_seconds: float
    model_used: str


class GenerateQuestionsRequest(BaseModel):
    doc_ids: Optional[List[str]] = None
    count: int = Field(default=5, ge=1, le=15)
    model: Optional[str] = None


class GenerateQuestionsResponse(BaseModel):
    questions: List[str]
    processing_time_seconds: float
    model_used: str


class QuizOption(BaseModel):
    key: str
    text: str


class QuizItem(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    citation: Optional[str] = None


class GenerateQuizRequest(BaseModel):
    doc_ids: Optional[List[str]] = None
    question_count: int = Field(default=5, ge=1, le=10)
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    model: Optional[str] = None


class GenerateQuizResponse(BaseModel):
    quiz: List[QuizItem]
    processing_time_seconds: float
    model_used: str


class FlashcardItem(BaseModel):
    id: str
    front: str
    back: str
    category: Optional[str] = "Key Concept"
    citation: Optional[str] = None


class GenerateFlashcardsRequest(BaseModel):
    doc_ids: Optional[List[str]] = None
    card_count: int = Field(default=6, ge=1, le=20)
    model: Optional[str] = None


class GenerateFlashcardsResponse(BaseModel):
    flashcards: List[FlashcardItem]
    processing_time_seconds: float
    model_used: str


class ResearchNoteCreateRequest(BaseModel):
    session_id: Optional[str] = None
    title: str = Field(min_length=1, max_length=200)
    content: str
    tags: List[str] = Field(default_factory=list)
    source_citations: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchNoteUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class ResearchNoteInfo(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str]
    title: str
    content: str
    tags: List[str]
    source_citations: List[Dict[str, Any]]
    created_at: str
    updated_at: str


