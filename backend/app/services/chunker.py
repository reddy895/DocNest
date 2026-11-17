import re
from typing import List
from pydantic import BaseModel
from backend.app.services.pdf_extractor import ExtractedPage
from backend.app.models.document import ChunkMetadata


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    char_count: int
    metadata: ChunkMetadata


def split_text_into_semantic_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 60,
) -> List[str]:
    """
    Split text into chunks aiming for chunk_size characters, respecting
    sentence terminators and paragraph breaks with overlapping windows.
    """
    text = text.strip()
    if not text:
        return []

    # If text is already smaller than chunk size, return immediately
    if len(text) <= chunk_size:
        return [text]

    # Split into sentences or lines
    # Match sentences ending with period, question mark, exclamation mark followed by space or newline
    sentence_end_regex = re.compile(r'(?<=[.!?])\s+|\n{2,}|\n')
    raw_segments = [s.strip() for s in sentence_end_regex.split(text) if s.strip()]

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for segment in raw_segments:
        segment_len = len(segment)

        # If a single segment is larger than chunk_size, hard-wrap it gracefully
        if segment_len > chunk_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0

            start = 0
            while start < segment_len:
                end = min(start + chunk_size, segment_len)
                if end < segment_len:
                    last_space = segment.rfind(" ", start, end)
                    if last_space > start:
                        end = last_space
                chunk_slice = segment[start:end].strip()
                if chunk_slice:
                    chunks.append(chunk_slice)
                start = max(start + 1, end - chunk_overlap)
            continue

        if current_len + segment_len + 1 <= chunk_size:
            current_chunk.append(segment)
            current_len += segment_len + 1
        else:
            if current_chunk:
                full_chunk = " ".join(current_chunk)
                chunks.append(full_chunk)

                # Keep overlap from the end of current_chunk for continuity
                overlap_tokens: List[str] = []
                overlap_len = 0
                for token in reversed(current_chunk):
                    if overlap_len + len(token) + 1 <= chunk_overlap:
                        overlap_tokens.insert(0, token)
                        overlap_len += len(token) + 1
                    else:
                        break
                current_chunk = overlap_tokens + [segment]
                current_len = sum(len(t) for t in current_chunk) + len(current_chunk) - 1
            else:
                current_chunk = [segment]
                current_len = segment_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c for c in chunks if c.strip()]


def create_document_chunks(
    doc_id: str,
    filename: str,
    file_hash: str,
    pages: List[ExtractedPage],
    chunk_size: int = 500,
    chunk_overlap: int = 60,
) -> List[DocumentChunk]:
    """
    Produce page-aware DocumentChunks across all extracted pages.
    Guarantees page isolation: page numbers are preserved directly on each chunk.
    """
    raw_chunks_data = []

    # First pass: collect per-page chunks
    for page in pages:
        if page.is_empty or not page.text.strip():
            continue

        page_text_chunks = split_text_into_semantic_chunks(
            page.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for p_idx, chunk_text in enumerate(page_text_chunks):
            raw_chunks_data.append((page.page_number, p_idx, chunk_text))

    total_chunks = len(raw_chunks_data)
    result_chunks: List[DocumentChunk] = []

    for global_idx, (page_num, p_idx, chunk_text) in enumerate(raw_chunks_data):
        chunk_id = f"{doc_id}_p{page_num}_c{p_idx}"
        char_count = len(chunk_text)

        meta = ChunkMetadata(
            doc_id=doc_id,
            chunk_id=chunk_id,
            filename=filename,
            page_number=page_num,
            chunk_index=global_idx,
            total_chunks_in_doc=max(1, total_chunks),
            char_count=char_count,
            file_hash=file_hash,
        )

        result_chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                filename=filename,
                page_number=page_num,
                chunk_index=global_idx,
                text=chunk_text,
                char_count=char_count,
                metadata=meta,
            )
        )

    return result_chunks
