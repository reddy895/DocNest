import io
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError

logger = logging.getLogger("docnest.extractor")

# Try to import Docling if available
HAS_DOCLING = False
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    HAS_DOCLING = True
    logger.info("IBM Docling document converter initialized successfully.")
except Exception as e:
    logger.info(f"IBM Docling not present or failed to load ({e}). Using optimized layout-aware fallback parser.")


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    char_count: int
    is_empty: bool
    headings: List[str] = []
    tables: List[str] = []


class ExtractionResult(BaseModel):
    filename: str
    page_count: int
    pages: List[ExtractedPage]
    markdown_content: Optional[str] = None
    is_scanned: bool = False
    total_chars: int = 0
    parser_used: str = "docling"
    error_message: Optional[str] = None


def extract_pdf_with_docling(file_bytes: bytes, filename: str) -> Optional[ExtractionResult]:
    """Attempt layout-aware structured Markdown extraction with IBM Docling."""
    if not HAS_DOCLING:
        return None
    try:
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        converter = DocumentConverter()
        doc_result = converter.convert(tmp_path)
        os.unlink(tmp_path)

        markdown_text = doc_result.document.export_to_markdown()
        pages: List[ExtractedPage] = []
        page_chunks = markdown_text.split("<!-- page break -->")
        if len(page_chunks) <= 1:
            page_chunks = [markdown_text]

        for idx, page_content in enumerate(page_chunks):
            page_num = idx + 1
            text_clean = page_content.strip()
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=text_clean,
                    char_count=len(text_clean),
                    is_empty=(len(text_clean) == 0),
                )
            )

        total_chars = len(markdown_text)
        page_count = max(len(pages), 1)
        is_scanned = total_chars < (page_count * 40)

        return ExtractionResult(
            filename=filename,
            page_count=page_count,
            pages=pages,
            markdown_content=markdown_text,
            is_scanned=is_scanned,
            total_chars=total_chars,
            parser_used="docling",
        )
    except Exception as exc:
        logger.warning(f"Docling extraction failed for '{filename}', falling back to fast layout parser: {exc}")
        return None


def extract_pdf_pages(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Extract text page-by-page from raw PDF bytes.
    First attempts Docling for layout-aware Markdown parsing, falling back to robust PyPDF.
    """
    # 1. Try Docling
    docling_result = extract_pdf_with_docling(file_bytes, filename)
    if docling_result and not docling_result.error_message and docling_result.total_chars > 0:
        return docling_result

    # 2. Fallback Fast Layout Parser
    try:
        stream = io.BytesIO(file_bytes)
        reader = PdfReader(stream)

        # Handle encryption
        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
                if decrypted == 0:
                    return ExtractionResult(
                        filename=filename,
                        page_count=0,
                        pages=[],
                        error_message="Document is password protected and cannot be decrypted.",
                    )
            except Exception as e:
                return ExtractionResult(
                    filename=filename,
                    page_count=0,
                    pages=[],
                    error_message=f"Encrypted document error: {str(e)}",
                )

        page_count = len(reader.pages)
        if page_count == 0:
            return ExtractionResult(
                filename=filename,
                page_count=0,
                pages=[],
                error_message="PDF contains no pages.",
            )

        extracted_pages: List[ExtractedPage] = []
        total_chars = 0
        full_markdown_parts = []

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                raw_text = page.extract_text() or ""
                cleaned_text = raw_text.replace("\x00", "").strip()
                char_count = len(cleaned_text)
                total_chars += char_count

                # Extract potential headings
                lines = cleaned_text.splitlines()
                headings = [line.strip() for line in lines if len(line.strip()) < 80 and line.strip().isupper() and len(line.strip()) > 3][:5]

                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=cleaned_text,
                        char_count=char_count,
                        is_empty=(char_count == 0),
                        headings=headings,
                    )
                )
                full_markdown_parts.append(f"## Page {page_num}\n\n{cleaned_text}")
            except Exception as page_err:
                logger.warning(f"Error extracting page {page_num} in '{filename}': {page_err}")
                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text="",
                        char_count=0,
                        is_empty=True,
                    )
                )

        is_scanned = (total_chars < (page_count * 40))

        return ExtractionResult(
            filename=filename,
            page_count=page_count,
            pages=extracted_pages,
            markdown_content="\n\n".join(full_markdown_parts),
            is_scanned=is_scanned,
            total_chars=total_chars,
            parser_used="pypdf_fast_parser",
            error_message=None,
        )

    except (PdfReadError, FileNotDecryptedError) as exc:
        logger.error(f"Failed to read PDF '{filename}': {exc}")
        return ExtractionResult(
            filename=filename,
            page_count=0,
            pages=[],
            error_message=f"Corrupt or unreadable PDF: {str(exc)}",
        )
    except Exception as exc:
        logger.error(f"Unexpected error extracting PDF '{filename}': {exc}", exc_info=True)
        return ExtractionResult(
            filename=filename,
            page_count=0,
            pages=[],
            error_message=f"Text extraction failed: {str(exc)}",
        )
