import pytest
from backend.app.services.pdf_extractor import extract_pdf_pages

def test_extract_corrupt_pdf():
    corrupt_bytes = b"%PDF-1.4 corrupt header without xref or trailer"
    res = extract_pdf_pages(corrupt_bytes, "corrupt.pdf")
    assert res.error_message is not None or res.page_count == 0

def test_extract_real_pdf():
    # Test with SE2.pdf located in downloads
    import os
    pdf_path = "/home/reddy895/Downloads/SE2.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        res = extract_pdf_pages(pdf_bytes, "SE2.pdf")
        assert res.page_count > 0
        assert len(res.pages) == res.page_count
        assert res.pages[0].page_number == 1
        assert res.total_chars > 0
        assert not res.is_scanned
