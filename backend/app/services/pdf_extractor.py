import io
import logging
from typing import List, Optional
from pydantic import BaseModel
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError

logger = logging.getLogger("docnest.extractor")


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    char_count: int
    is_empty: bool


class ExtractionResult(BaseModel):
    filename: str
    page_count: int
    pages: List[ExtractedPage]
    is_scanned: bool = False
    total_chars: int = 0
    error_message: Optional[str] = None


def extract_pdf_pages(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Extract text page-by-page from raw PDF bytes.
    Preserves exact 1-based page numbers, detects scanned documents,
    and isolates errors per page.
    """
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

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                raw_text = page.extract_text() or ""
                # Normalize excessive whitespace and null characters
                cleaned_text = raw_text.replace("\x00", "").strip()
                char_count = len(cleaned_text)
                total_chars += char_count

                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=cleaned_text,
                        char_count=char_count,
                        is_empty=(char_count == 0),
                    )
                )
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

        # Detect if document appears to be scanned (average < 40 chars per page)
        is_scanned = (total_chars < (page_count * 40))

        return ExtractionResult(
            filename=filename,
            page_count=page_count,
            pages=extracted_pages,
            is_scanned=is_scanned,
            total_chars=total_chars,
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
