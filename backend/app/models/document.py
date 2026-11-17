from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """
    Metadata attached to every vectorized chunk in ChromaDB.
    Enforces strict page awareness and source traceability.
    """
    doc_id: str
    chunk_id: str
    filename: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    total_chunks_in_doc: int = Field(ge=1)
    char_count: int
    file_hash: str

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert to Chroma-compatible flat dictionary."""
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "filename": self.filename,
            "page_number": int(self.page_number),
            "chunk_index": int(self.chunk_index),
            "total_chunks_in_doc": int(self.total_chunks_in_doc),
            "char_count": int(self.char_count),
            "file_hash": self.file_hash,
            # Source attribution string for grounding citations
            "source": f"{self.filename} (Page {self.page_number})",
        }

    @classmethod
    def from_chroma_metadata(cls, meta: Dict[str, Any]) -> "ChunkMetadata":
        return cls(
            doc_id=str(meta.get("doc_id", "")),
            chunk_id=str(meta.get("chunk_id", "")),
            filename=str(meta.get("filename", "")),
            page_number=int(meta.get("page_number", 1)),
            chunk_index=int(meta.get("chunk_index", 0)),
            total_chunks_in_doc=int(meta.get("total_chunks_in_doc", 1)),
            char_count=int(meta.get("char_count", 0)),
            file_hash=str(meta.get("file_hash", "")),
        )


class DocumentRecord(BaseModel):
    """
    Master record for an indexed PDF document in DocNest.
    """
    doc_id: str
    filename: str
    file_hash: str
    file_size_bytes: int
    page_count: int
    total_chunks: int
    is_scanned: bool = False
    upload_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    file_path: Optional[str] = None
    status: str = "indexed"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
