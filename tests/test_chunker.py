import pytest
from backend.app.services.chunker import split_text_into_semantic_chunks, create_document_chunks
from backend.app.services.pdf_extractor import ExtractedPage

def test_split_empty_text():
    assert split_text_into_semantic_chunks("") == []
    assert split_text_into_semantic_chunks("   ") == []

def test_split_short_text():
    text = "Short sentence that fits into one chunk."
    chunks = split_text_into_semantic_chunks(text, chunk_size=200, chunk_overlap=30)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_sentence_boundary_preservation():
    text = (
        "Retrieval-Augmented Generation enhances LLM reliability. "
        "It grounds answers strictly in provided source passages. "
        "Page citations ensure full auditability for enterprise users."
    )
    chunks = split_text_into_semantic_chunks(text, chunk_size=80, chunk_overlap=20)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 120  # Allows slight boundary buffer

def test_create_document_chunks_preserves_pages():
    pages = [
        ExtractedPage(page_number=1, text="Page 1 header. Introduction to DocNest.", char_count=40, is_empty=False),
        ExtractedPage(page_number=2, text="Page 2 body. Technical specifications and benchmarks.", char_count=52, is_empty=False),
    ]
    chunks = create_document_chunks(
        doc_id="doc_test_123",
        filename="test_doc.pdf",
        file_hash="hash123",
        pages=pages,
        chunk_size=100,
        chunk_overlap=20,
    )
    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
    assert chunks[0].metadata.source == "test_doc.pdf (Page 1)"
    assert chunks[1].metadata.source == "test_doc.pdf (Page 2)"
