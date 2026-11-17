import io
from typing import List, Dict, Any
from pypdf import PdfReader
from backend.app.services.pdf_extractor import extract_pdf_pages
from backend.app.services.chunker import split_text_into_semantic_chunks


def extract_text(file: Any) -> List[Dict[str, Any]]:
    """
    Extract text per page from file object or bytes.
    Returns [{'page': 1, 'text': '...'}]
    """
    if hasattr(file, "read"):
        file.seek(0)
        content = file.read()
    elif isinstance(file, bytes):
        content = file
    else:
        with open(file, "rb") as f:
            content = f.read()

    res = extract_pdf_pages(content, getattr(file, "name", "document.pdf"))
    return [{"page": p.page_number, "text": p.text} for p in res.pages]


def split_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks.
    """
    return split_text_into_semantic_chunks(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
