import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

from backend.app.services.pdf_extractor import (
    extract_document_content,
    ExtractionResult,
    ExtractedPage,
)

logger = logging.getLogger("docnest.ingest.router")


class DocumentFormatMeta(BaseModel):
    extension: str
    mime_type: str
    is_supported: bool
    parser_type: str
    description: str


class IngestionDocument(BaseModel):
    filename: str
    format: str
    page_count: int
    total_characters: int
    is_scanned: bool = False
    pages: List[ExtractedPage]
    markdown_content: Optional[str] = None
    parser_used: str
    error: Optional[str] = None


class DocumentIngestionRouter:
    """
    Layout-aware document ingestion router supporting PDF, DOCX, TXT, MD, and CSV.
    Directs incoming documents to appropriate structured parsers while preserving
    layout geometry, headings, tables, and page metadata.
    """

    SUPPORTED_FORMATS: Dict[str, DocumentFormatMeta] = {
        ".pdf": DocumentFormatMeta(
            extension=".pdf",
            mime_type="application/pdf",
            is_supported=True,
            parser_type="docling_pypdf_hybrid",
            description="Layout-aware PDF parsing with table preservation and OCR fallback",
        ),
        ".docx": DocumentFormatMeta(
            extension=".docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            is_supported=True,
            parser_type="python_docx",
            description="Microsoft Word documents with heading hierarchy and table extraction",
        ),
        ".txt": DocumentFormatMeta(
            extension=".txt",
            mime_type="text/plain",
            is_supported=True,
            parser_type="utf8_plain",
            description="Plain text files partitioned along paragraph boundaries",
        ),
        ".md": DocumentFormatMeta(
            extension=".md",
            mime_type="text/markdown",
            is_supported=True,
            parser_type="markdown_structure",
            description="Markdown documents preserving header hierarchies and tables",
        ),
        ".csv": DocumentFormatMeta(
            extension=".csv",
            mime_type="text/csv",
            is_supported=True,
            parser_type="csv_table_parser",
            description="Tabular CSV data transformed into markdown data tables",
        ),
    }

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Return list of supported file extensions."""
        return list(cls.SUPPORTED_FORMATS.keys())

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Check if filename has a supported extension."""
        ext = Path(filename).suffix.lower()
        return ext in cls.SUPPORTED_FORMATS

    def route_and_extract(self, file_bytes: bytes, filename: str) -> IngestionDocument:
        """
        Route incoming file buffer to appropriate structure-preserving parser.
        """
        ext = Path(filename).suffix.lower()
        if not self.is_supported(filename):
            allowed = ", ".join(self.get_supported_extensions())
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: {allowed}")

        meta = self.SUPPORTED_FORMATS[ext]
        logger.info(f"Routing '{filename}' ({len(file_bytes)} bytes) to parser '{meta.parser_type}'...")

        result: ExtractionResult = extract_document_content(file_bytes, filename)

        return IngestionDocument(
            filename=filename,
            format=ext,
            page_count=result.page_count,
            total_characters=result.total_chars,
            is_scanned=result.is_scanned,
            pages=result.pages,
            markdown_content=result.markdown_content,
            parser_used=result.parser_used,
            error=result.error_message,
        )


_ingest_router: Optional[DocumentIngestionRouter] = None


def get_document_router() -> DocumentIngestionRouter:
    """Singleton accessor for DocumentIngestionRouter."""
    global _ingest_router
    if _ingest_router is None:
        _ingest_router = DocumentIngestionRouter()
    return _ingest_router
