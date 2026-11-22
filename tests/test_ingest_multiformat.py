import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.database import db_manager, get_db_connection
from backend.app.services.document_router import get_document_router
from backend.app.services.chunker import create_document_chunks
from backend.app.services.ocr_service import get_ocr_service
from backend.app.services.table_extractor import get_table_extractor
from backend.app.services.pdf_extractor import ExtractedPage


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    await db_manager.init_db()
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (id, email, username, password_hash)
            VALUES ('user_default_local', 'local@docnest.ai', 'Local Operator', 'hashed_local_pass')
            """
        )
        await db.commit()


@pytest.mark.asyncio
async def test_markdown_and_txt_parsing():
    router = get_document_router()
    
    # 1. Test TXT parsing
    txt_content = b"Line 1 of raw text.\nLine 2 of research document.\nLine 3 conclusions."
    doc = router.route_and_extract(txt_content, "notes.txt")
    assert len(doc.pages) >= 1
    assert "Line 1 of raw text" in doc.pages[0].text
    assert doc.pages[0].page_number == 1

    # 2. Test Markdown parsing with headers
    md_content = b"# Introduction\nDocNest is an AI research workspace.\n\n## Architecture\nRAG pipeline combines Chroma and BM25."
    doc_md = router.route_and_extract(md_content, "architecture.md")
    assert len(doc_md.pages) >= 1
    assert "# Introduction" in doc_md.pages[0].text
    assert "DocNest is an AI research workspace" in doc_md.pages[0].text


@pytest.mark.asyncio
async def test_csv_table_preservation():
    router = get_document_router()
    csv_bytes = b"Model,Accuracy,Latency\nLlama3.2,89.5,45ms\nMistral,87.2,52ms"
    doc_csv = router.route_and_extract(csv_bytes, "benchmark.csv")
    assert len(doc_csv.pages) >= 1
    assert "Model" in doc_csv.pages[0].text
    assert "Llama3.2" in doc_csv.pages[0].text


@pytest.mark.asyncio
async def test_structure_aware_chunking_with_sections():
    pages = [
        ExtractedPage(
            page_number=1,
            text="# Executive Summary\nDocNest delivers fast and accurate RAG responses.\n\n# System Capabilities\nSupports multi-modal search and cross-encoder reranking.",
            char_count=130,
            is_empty=False,
        )
    ]
    chunks = create_document_chunks("doc_test_123", "summary.md", "mock_hash_123", pages, chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 1
    assert chunks[0].doc_id == "doc_test_123"
    assert chunks[0].filename == "summary.md"
    assert chunks[0].page_number == 1
    assert len(chunks[0].text) > 0


@pytest.mark.asyncio
async def test_ocr_service_fallback():
    ocr = get_ocr_service()
    assert hasattr(ocr, "is_page_likely_scanned")
    assert hasattr(ocr, "compute_heuristic_confidence")
    # Low density text is identified as scan
    is_scan = ocr.is_page_likely_scanned("ab", page_has_images=False)
    assert is_scan is True
    # Normal dense text is not scanned
    is_not_scan = ocr.is_page_likely_scanned("This is a standard full paragraph of digital text extracted from a searchable document with high character density.", page_has_images=False)
    assert is_not_scan is False


@pytest.mark.asyncio
async def test_table_extractor_markdown_conversion():
    extractor = get_table_extractor()
    raw_text = "Product    Qty    Price\nServer A   4      $1200\nServer B   2      $2400"
    out_text, tables = extractor.extract_tables_from_text(raw_text)
    assert len(tables) >= 1
    assert "|" in tables[0].markdown_table
    assert "Server A" in tables[0].markdown_table


@pytest.mark.asyncio
async def test_document_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/documents/non_existent_doc/status")
        assert resp.status_code == 404
