import io
from typing import List, Dict, Any
from pypdf import PdfReader


def extract_text(file: Any) -> List[Dict[str, Any]]:
    """
    Extract text per page from an uploaded PDF file or file path.
    Returns a list of dicts: [{'page': 1, 'text': '...'}, ...]
    """
    if hasattr(file, "read"):
        file.seek(0)
        reader = PdfReader(file)
    elif isinstance(file, bytes):
        reader = PdfReader(io.BytesIO(file))
    else:
        reader = PdfReader(file)

    pages = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({
            "page": idx + 1,
            "text": text
        })
    return pages


def split_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks of roughly `chunk_size` characters with `chunk_overlap`.
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    total_length = len(text)

    while start < total_length:
        end = min(start + chunk_size, total_length)
        if end < total_length:
            break_pt = text.rfind("\n", start, end)
            if break_pt == -1 or break_pt <= start:
                break_pt = text.rfind(" ", start, end)
            if break_pt > start:
                end = break_pt

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= total_length:
            break

        start = max(start + 1, end - chunk_overlap)

    return chunks

