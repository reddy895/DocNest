from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserPreferences(BaseModel):
    theme: str = "dark"
    default_model: str = "llama3.2"
    retrieval_top_k: int = 5
    min_confidence_score: float = 0.30
    hybrid_search_enabled: bool = True
    notifications_enabled: bool = True


class MongoUser(BaseModel):
    id: str
    email: str
    username: str
    hashed_password: str
    full_name: str = ""
    avatar_url: Optional[str] = None
    role: str = "researcher"
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class MongoWorkspace(BaseModel):
    id: str
    user_id: str
    name: str
    description: str = ""
    color: str = "#F5C542"
    document_ids: List[str] = Field(default_factory=list)
    is_default: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class MongoDocument(BaseModel):
    id: str
    user_id: str
    workspace_id: str = "default_workspace"
    filename: str
    file_hash: str
    file_size_bytes: int
    page_count: int = 1
    total_chunks: int = 0
    status: str = "ready"  # queued | parsing | chunking | embedding | ready | failed
    progress_pct: int = 100
    error_msg: str = ""
    is_scanned: bool = False
    tags: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class MongoMessageCitation(BaseModel):
    source_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    relevance_score: float = 0.50
    section_heading: Optional[str] = None


class MongoMessage(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    sender: str  # 'user' | 'assistant' | 'system'
    text: str
    citations: List[MongoMessageCitation] = Field(default_factory=list)
    retrieval_trace: Dict[str, Any] = Field(default_factory=dict)
    feedback_rating: Optional[int] = None  # 1 for up, -1 for down
    feedback_comment: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)


class MongoConversation(BaseModel):
    id: str
    user_id: str
    workspace_id: str = "default_workspace"
    title: str = "New Research"
    is_pinned: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class MongoResearchNote(BaseModel):
    id: str
    user_id: str
    workspace_id: str = "default_workspace"
    conversation_id: Optional[str] = None
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class MongoProcessingJob(BaseModel):
    id: str
    doc_id: str
    user_id: str
    status: str = "queued"
    progress_pct: int = 0
    stage: str = "validation"
    error_msg: str = ""
    started_at: str = Field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None
