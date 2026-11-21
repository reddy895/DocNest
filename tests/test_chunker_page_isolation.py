from backend.app.services.chunker import create_document_chunks
from backend.app.services.pdf_extractor import ExtractedPage


def test_empty_pages_are_skipped_without_losing_page_numbers():
    pages = [
        ExtractedPage(
            page_number=1,
            text="First page content.",
            char_count=19,
            is_empty=False,
        ),
        ExtractedPage(page_number=2, text="   ", char_count=0, is_empty=True),
        ExtractedPage(
            page_number=3,
            text="Third page content.",
            char_count=19,
            is_empty=False,
        ),
    ]

    chunks = create_document_chunks(
        doc_id="doc_pages",
        filename="pages.pdf",
        file_hash="hash",
        pages=pages,
    )

    assert [chunk.page_number for chunk in chunks] == [1, 3]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert all(chunk.metadata.total_chunks_in_doc == 2 for chunk in chunks)
