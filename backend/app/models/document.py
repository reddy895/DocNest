from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """
    Metadata attached to every vectorized chunk in ChromaDB.
    Enforces strict page awareness, workspace isolation, and source traceability.
    """
    doc_id: str
    chunk_id: str
    filename: str
    user_id: str = "user_default_local"
    workspace_id: str = "Default Workspace"
    section_heading: Optional[str] = None
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    total_chunks_in_doc: int = Field(ge=1)
    char_count: int
    file_hash: str

    @property
    def source(self) -> str:
        return f"{self.filename} (Page {self.page_number})"

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert to Chroma-compatible flat dictionary."""
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "filename": self.filename,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "section_heading": self.section_heading or "",
            "page_number": int(self.page_number),
            "chunk_index": int(self.chunk_index),
            "total_chunks_in_doc": int(self.total_chunks_in_doc),
            "char_count": int(self.char_count),
            "file_hash": self.file_hash,
            "source": f"{self.filename} (Page {self.page_number})",
        }

    @classmethod
    def from_chroma_metadata(cls, meta: Dict[str, Any]) -> "ChunkMetadata":
        return cls(
            doc_id=str(meta.get("doc_id", "")),
            chunk_id=str(meta.get("chunk_id", "")),
            filename=str(meta.get("filename", "")),
            user_id=str(meta.get("user_id", "user_default_local")),
            workspace_id=str(meta.get("workspace_id", "Default Workspace")),
            section_heading=str(meta.get("section_heading", "")) or None,
            page_number=int(meta.get("page_number", 1)),
            chunk_index=int(meta.get("chunk_index", 0)),
            total_chunks_in_doc=int(meta.get("total_chunks_in_doc", 1)),
            char_count=int(meta.get("char_count", 0)),
            file_hash=str(meta.get("file_hash", "")),
        )


class DocumentRecord(BaseModel):
    """
    Master record for an indexed PDF/document in DocNest.
    """
    doc_id: str
    user_id: str = "user_default_local"
    workspace_id: str = "Default Workspace"
    filename: str
    file_hash: str
    file_size_bytes: int
    page_count: int
    total_chunks: int
    status: str = "ready"
    progress_pct: int = 100
    error_msg: Optional[str] = None
    is_scanned: bool = False
    tags: List[str] = Field(default_factory=list)
    upload_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
