import pytest
from backend.app.services.validator import validate_pdf_content, sanitize_filename, compute_sha256

def test_sanitize_filename():
    assert sanitize_filename("my report.pdf") == "my report.pdf"
    assert sanitize_filename("../../../etc/passwd") == "passwd.pdf"
    assert sanitize_filename("weird!@#name.pdf") == "weird___name.pdf"
    assert sanitize_filename("noextension") == "noextension.pdf"

def test_validate_empty_file():
    res = validate_pdf_content("empty.pdf", b"")
    assert not res.is_valid
    assert "empty" in res.error_message.lower()

def test_validate_non_pdf_extension():
    res = validate_pdf_content("script.sh", b"%PDF-1.4 content")
    # sanitize_filename forces .pdf if missing or replaces, but test with explicit mismatch
    res2 = validate_pdf_content("bad.txt", b"not a pdf")
    assert not res2.is_valid

def test_validate_magic_bytes_missing():
    res = validate_pdf_content("fake.pdf", b"GIF89a fake image header")
    assert not res.is_valid
    assert "magic bytes" in res.error_message.lower()

def test_validate_valid_pdf_header():
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj"
    res = validate_pdf_content("valid.pdf", content)
    assert res.is_valid
    assert res.file_size_bytes == len(content)
    assert res.file_hash == compute_sha256(content)
