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


class DocumentInfo(BaseModel):
    """Metadata for an uploaded document."""
    doc_id: str
    filename: str
    file_size_bytes: int
    file_hash: str
    page_count: int
    total_chunks: int
    upload_date: str
    status: str = "indexed"
    is_scanned: bool = False


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


class ChatQueryRequest(BaseModel):
    """Incoming user question request."""
    question: str = Field(min_length=1, max_length=2000)
    doc_id: Optional[str] = None
    top_k: Optional[int] = Field(default=4, ge=1, le=12)
    similarity_threshold: Optional[float] = Field(default=0.25, ge=0.0, le=1.0)


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
