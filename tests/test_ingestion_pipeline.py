import pytest
from backend.app.services.pdf_extractor import (
    extract_pdf_pages,
    detect_and_format_tables,
    ExtractedPage,
)
from backend.app.services.chunker import (
    split_markdown_into_structured_chunks,
    create_document_chunks,
)
from backend.app.models.document import ChunkMetadata


def test_table_structure_detection():
    sample_text = """
    Business Segment    Q3 Revenue    Gross Margin
    Enterprise Subs     $86.4M        78.4%
    Services            $24.2M        42.0%
    """
    _, tables = detect_and_format_tables(sample_text)
    assert len(tables) >= 1
    assert "|" in tables[0]
    assert "Enterprise Subs" in tables[0]


def test_markdown_heading_chunking():
    md = """# Architecture Overview
This is the main introduction to the enterprise RAG system.

## Ingestion Pipeline
The ingestion pipeline converts PDFs to markdown and preserves headings.

### Chunking Logic
Chunks are generated with 512 tokens and 64 token overlap.
"""
    chunks = split_markdown_into_structured_chunks(md, chunk_size=200, chunk_overlap=30)
    assert len(chunks) >= 3

    headings = [h for _, h in chunks if h]
    assert "Architecture Overview" in headings or "Ingestion Pipeline" in headings or "Chunking Logic" in headings


def test_document_chunks_metadata_preservation():
    pages = [
        ExtractedPage(
            page_number=1,
            text="# Financial Highlights\nTotal revenue grew by 28% year-over-year.",
            char_count=60,
            is_empty=False,
            headings=["Financial Highlights"],
        ),
        ExtractedPage(
            page_number=2,
            text="## Risk Analysis\nSupply chain constraints may impact delivery timelines.",
            char_count=70,
            is_empty=False,
            headings=["Risk Analysis"],
        ),
    ]

    doc_chunks = create_document_chunks(
        doc_id="doc_test_123",
        filename="report.pdf",
        file_hash="hash_12345",
        pages=pages,
        chunk_size=100,
        chunk_overlap=20,
        user_id="user_test",
        workspace_id="Test Workspace",
    )

    assert len(doc_chunks) >= 2
    for chunk in doc_chunks:
        assert chunk.doc_id == "doc_test_123"
        assert chunk.filename == "report.pdf"
        assert chunk.page_number in [1, 2]
        assert chunk.metadata.user_id == "user_test"
        assert chunk.metadata.workspace_id == "Test Workspace"
        assert chunk.metadata.total_chunks_in_doc == len(doc_chunks)
        chroma_dict = chunk.metadata.to_chroma_metadata()
        assert "source" in chroma_dict
        assert "section_heading" in chroma_dict
