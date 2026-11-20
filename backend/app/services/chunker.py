import re
import logging
from typing import List, Optional, Tuple
from pydantic import BaseModel
from backend.app.services.pdf_extractor import ExtractedPage
from backend.app.models.document import ChunkMetadata

logger = logging.getLogger("docnest.chunker")


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

    if len(text) <= chunk_size:
        return [text]

    # Split into sentences or lines
    sentence_end_regex = re.compile(r'(?<=[.!?])\s+|\n{2,}|\n')
    raw_segments = [s.strip() for s in sentence_end_regex.split(text) if s.strip()]

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for segment in raw_segments:
        segment_len = len(segment)

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

                # Overlap tokens
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


def split_markdown_into_structured_chunks(
    markdown_text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[Tuple[str, Optional[str]]]:
    """
    Split markdown text on structural boundaries (headers, paragraphs) while tracking section headings.
    Preserves table blocks intact when possible.
    """
    if not markdown_text or not markdown_text.strip():
        return []

    lines = markdown_text.splitlines()
    sections: List[Tuple[Optional[str], List[str]]] = []
    current_heading = None
    current_lines: List[str] = []
    in_table = False

    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            in_table = True
        elif in_table and not s.startswith("|"):
            in_table = False

        header_match = re.match(r'^(#{1,4})\s+(.+)$', s)
        if header_match and not in_table:
            if current_lines:
                sections.append((current_heading, current_lines))
                current_lines = []
            current_heading = header_match.group(2).strip()
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    result_chunks: List[Tuple[str, Optional[str]]] = []

    for heading, sec_lines in sections:
        section_text = "\n".join(sec_lines).strip()
        if not section_text:
            continue
        sub_chunks = split_text_into_semantic_chunks(section_text, chunk_size, chunk_overlap)
        for sc in sub_chunks:
            result_chunks.append((sc, heading))

    return result_chunks


class RecursiveStructureAwareChunker:
    """
    Recursive structure-aware chunker with section heading attribution,
    table integrity preservation, and token/character bounding.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        doc_id: str,
        filename: str,
        file_hash: str,
        pages: List[ExtractedPage],
        user_id: str = "user_default_local",
        workspace_id: str = "Default Workspace",
    ) -> List[DocumentChunk]:
        """
        Process extracted document pages into page-isolated, structure-preserving DocumentChunks.
        """
        raw_chunks_data = []

        for page in pages:
            if page.is_empty or not page.text.strip():
                continue

            has_md_headers = bool(re.search(r'^(#{1,4})\s+', page.text, re.MULTILINE))
            page_heading = page.headings[0] if (hasattr(page, "headings") and page.headings) else None

            if has_md_headers:
                structured = split_markdown_into_structured_chunks(
                    page.text,
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
                for p_idx, (chunk_text, heading) in enumerate(structured):
                    raw_chunks_data.append((page.page_number, p_idx, chunk_text, heading or page_heading))
            else:
                page_text_chunks = split_text_into_semantic_chunks(
                    page.text,
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
                for p_idx, chunk_text in enumerate(page_text_chunks):
                    raw_chunks_data.append((page.page_number, p_idx, chunk_text, page_heading))

        total_chunks = len(raw_chunks_data)
        result_chunks: List[DocumentChunk] = []

        for global_idx, (page_num, p_idx, chunk_text, heading) in enumerate(raw_chunks_data):
            chunk_id = f"{doc_id}_p{page_num}_c{p_idx}"
            char_count = len(chunk_text)

            meta = ChunkMetadata(
                doc_id=doc_id,
                chunk_id=chunk_id,
                filename=filename,
                user_id=user_id,
                workspace_id=workspace_id,
                section_heading=heading,
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


def create_document_chunks(
    doc_id: str,
    filename: str,
    file_hash: str,
    pages: List[ExtractedPage],
    chunk_size: int = 500,
    chunk_overlap: int = 60,
    user_id: str = "user_default_local",
    workspace_id: str = "Default Workspace",
) -> List[DocumentChunk]:
    """Compatibility wrapper for create_document_chunks."""
    chunker = RecursiveStructureAwareChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_document(
        doc_id=doc_id,
        filename=filename,
        file_hash=file_hash,
        pages=pages,
        user_id=user_id,
        workspace_id=workspace_id,
    )
