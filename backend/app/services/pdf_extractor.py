import io
import csv
import re
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
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


def format_as_markdown_table(lines: List[str]) -> str:
    """Format whitespace or tab separated lines into a GitHub markdown table."""
    rows = []
    for line in lines:
        if "|" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
        elif "\t" in line:
            cells = [c.strip() for c in line.split("\t") if c.strip()]
        else:
            cells = [c.strip() for c in re.split(r"\s{2,}", line.strip()) if c.strip()]
        if cells:
            rows.append(cells)
    if not rows:
        return "\n".join(lines)
    max_cols = max(len(r) for r in rows)
    formatted = []
    header = rows[0] + [""] * (max_cols - len(rows[0]))
    formatted.append("| " + " | ".join(header) + " |")
    formatted.append("| " + " | ".join(["---"] * max_cols) + " |")
    for r in rows[1:]:
        padded = r + [""] * (max_cols - len(r))
        formatted.append("| " + " | ".join(padded) + " |")
    return "\n".join(formatted)


def detect_and_format_tables(text: str) -> tuple[str, List[str]]:
    """Detect ASCII or markdown tables in text and format them cleanly."""
    lines = text.splitlines()
    tables = []
    table_block = []
    in_table = False

    for line in lines:
        if "|" in line or "\t" in line or ("  " in line and len(line.split()) >= 3):
            in_table = True
            table_block.append(line)
        else:
            if in_table and len(table_block) >= 2:
                tables.append(format_as_markdown_table(table_block))
            table_block = []
            in_table = False

    if in_table and len(table_block) >= 2:
        tables.append(format_as_markdown_table(table_block))

    return text, tables


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
            page_chunks = markdown_text.split("\n## ")

        for idx, chunk in enumerate(page_chunks):
            p_text = chunk.strip()
            if not p_text and len(page_chunks) > 1:
                continue
            p_num = idx + 1
            headings = [line.strip("# ").strip() for line in p_text.splitlines() if line.strip().startswith("#")][:5]
            _, tables = detect_and_format_tables(p_text)
            pages.append(
                ExtractedPage(
                    page_number=p_num,
                    text=p_text,
                    char_count=len(p_text),
                    is_empty=len(p_text) == 0,
                    headings=headings,
                    tables=tables,
                )
            )

        if not pages:
            pages = [ExtractedPage(page_number=1, text=markdown_text, char_count=len(markdown_text), is_empty=False)]

        return ExtractionResult(
            filename=filename,
            page_count=len(pages),
            pages=pages,
            markdown_content=markdown_text,
            is_scanned=False,
            total_chars=len(markdown_text),
            parser_used="ibm_docling",
            error_message=None,
        )
    except Exception as exc:
        logger.warning(f"Docling extraction failed for '{filename}', falling back to PyPDF: {exc}")
        return None


def extract_docx(file_bytes: bytes, filename: str) -> ExtractionResult:
    """Extract structured paragraphs, headings, and tables from DOCX files."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        pages: List[ExtractedPage] = []
        current_page_lines: List[str] = []
        current_headings: List[str] = []
        current_tables: List[str] = []
        page_num = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            if para.style and "heading" in para.style.name.lower():
                current_headings.append(text)
                current_page_lines.append(f"### {text}\n")
            else:
                current_page_lines.append(text)

            # Paginate roughly every 2500 characters
            joined = "\n".join(current_page_lines)
            if len(joined) > 2500:
                pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=joined,
                        char_count=len(joined),
                        is_empty=False,
                        headings=current_headings,
                        tables=current_tables,
                    )
                )
                page_num += 1
                current_page_lines = []
                current_headings = []
                current_tables = []

        # Process docx tables
        for table in doc.tables:
            table_lines = []
            for row in table.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                table_lines.append("| " + " | ".join(cells) + " |")
            if table_lines:
                tbl_str = "\n".join(table_lines)
                current_tables.append(tbl_str)
                current_page_lines.append(f"\n{tbl_str}\n")

        # Final page
        joined_final = "\n".join(current_page_lines)
        if joined_final or not pages:
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=joined_final,
                    char_count=len(joined_final),
                    is_empty=len(joined_final) == 0,
                    headings=current_headings,
                    tables=current_tables,
                )
            )

        total_chars = sum(p.char_count for p in pages)
        full_md = "\n\n".join(f"## Page {p.page_number}\n\n{p.text}" for p in pages)

        return ExtractionResult(
            filename=filename,
            page_count=len(pages),
            pages=pages,
            markdown_content=full_md,
            is_scanned=False,
            total_chars=total_chars,
            parser_used="python_docx",
            error_message=None,
        )
    except Exception as exc:
        logger.error(f"Failed to extract DOCX '{filename}': {exc}", exc_info=True)
        return ExtractionResult(
            filename=filename,
            page_count=0,
            pages=[],
            error_message=f"DOCX extraction failed: {str(exc)}",
        )


def extract_txt_or_md(file_bytes: bytes, filename: str) -> ExtractionResult:
    """Extract plain text or Markdown files with structure preservation."""
    try:
        # Decode UTF-8 with fallback
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")

        content = content.replace("\r\n", "\n").strip()
        if not content:
            return ExtractionResult(
                filename=filename,
                page_count=0,
                pages=[],
                error_message="File is empty.",
            )

        # Chunk into logical pages of ~2000 chars along paragraph boundaries
        paragraphs = content.split("\n\n")
        pages: List[ExtractedPage] = []
        current_chunk = []
        current_len = 0
        page_num = 1

        for para in paragraphs:
            current_chunk.append(para)
            current_len += len(para) + 2
            if current_len >= 2000:
                page_text = "\n\n".join(current_chunk)
                headings = [line.strip("# ").strip() for line in page_text.splitlines() if line.strip().startswith("#")][:5]
                pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=page_text,
                        char_count=len(page_text),
                        is_empty=False,
                        headings=headings,
                    )
                )
                page_num += 1
                current_chunk = []
                current_len = 0

        if current_chunk:
            page_text = "\n\n".join(current_chunk)
            headings = [line.strip("# ").strip() for line in page_text.splitlines() if line.strip().startswith("#")][:5]
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=page_text,
                    char_count=len(page_text),
                    is_empty=False,
                    headings=headings,
                )
            )

        total_chars = len(content)
        return ExtractionResult(
            filename=filename,
            page_count=len(pages),
            pages=pages,
            markdown_content=content,
            is_scanned=False,
            total_chars=total_chars,
            parser_used="text_markdown_parser",
            error_message=None,
        )
    except Exception as exc:
        logger.error(f"Failed to extract TXT/MD '{filename}': {exc}", exc_info=True)
        return ExtractionResult(
            filename=filename,
            page_count=0,
            pages=[],
            error_message=f"Text extraction failed: {str(exc)}",
        )


def extract_csv(file_bytes: bytes, filename: str) -> ExtractionResult:
    """Extract CSV tabular data and format into readable markdown tables."""
    try:
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")

        stream = io.StringIO(content.strip())
        reader = csv.reader(stream)
        rows = list(reader)

        if not rows:
            return ExtractionResult(
                filename=filename,
                page_count=0,
                pages=[],
                error_message="CSV file contains no data.",
            )

        header = rows[0]
        data_rows = rows[1:]

        # Format rows into markdown tables per 30 rows
        chunk_size = 30
        pages: List[ExtractedPage] = []
        page_num = 1

        for start_idx in range(0, len(data_rows), chunk_size):
            batch = data_rows[start_idx : start_idx + chunk_size]
            table_lines = [
                "| " + " | ".join(header) + " |",
                "| " + " | ".join(["---"] * len(header)) + " |",
            ]
            for r in batch:
                # pad or truncate row to header length
                padded_r = (r + [""] * len(header))[:len(header)]
                clean_cells = [c.replace("|", "/").replace("\n", " ") for c in padded_r]
                table_lines.append("| " + " | ".join(clean_cells) + " |")

            table_text = f"### Table Part {page_num} (Rows {start_idx + 1}-{start_idx + len(batch)})\n\n" + "\n".join(table_lines)
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=table_text,
                    char_count=len(table_text),
                    is_empty=False,
                    headings=[f"Table Part {page_num}"],
                    tables=["\n".join(table_lines)],
                )
            )
            page_num += 1

        if not pages:
            single_page = "| " + " | ".join(header) + " |\n| " + " | ".join(["---"] * len(header)) + " |"
            pages.append(ExtractedPage(page_number=1, text=single_page, char_count=len(single_page), is_empty=False))

        total_chars = sum(p.char_count for p in pages)
        full_md = "\n\n".join(p.text for p in pages)

        return ExtractionResult(
            filename=filename,
            page_count=len(pages),
            pages=pages,
            markdown_content=full_md,
            is_scanned=False,
            total_chars=total_chars,
            parser_used="csv_table_parser",
            error_message=None,
        )
    except Exception as exc:
        logger.error(f"Failed to extract CSV '{filename}': {exc}", exc_info=True)
        return ExtractionResult(
            filename=filename,
            page_count=0,
            pages=[],
            error_message=f"CSV extraction failed: {str(exc)}",
        )


def extract_document_content(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Universal multi-format document parser supporting PDF, DOCX, TXT, MD, and CSV.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".docx":
        return extract_docx(file_bytes, filename)
    elif ext in [".txt", ".md"]:
        return extract_txt_or_md(file_bytes, filename)
    elif ext == ".csv":
        return extract_csv(file_bytes, filename)

    # Default to PDF parsing
    return extract_pdf_pages(file_bytes, filename)


def extract_pdf_pages(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Extract pages from PDF using IBM Docling if available, falling back to layout-aware PyPDF.
    """
    ext = Path(filename).suffix.lower()
    if ext in [".docx", ".txt", ".md", ".csv"]:
        return extract_document_content(file_bytes, filename)

    # 1. Try IBM Docling first
    docling_result = extract_pdf_with_docling(file_bytes, filename)
    if docling_result is not None and docling_result.page_count > 0:
        return docling_result

    # 2. Layout-aware PyPDF fallback
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
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

                lines = cleaned_text.splitlines()
                headings = [line.strip() for line in lines if len(line.strip()) < 80 and line.strip().isupper() and len(line.strip()) > 3][:5]
                _, tables = detect_and_format_tables(cleaned_text)

                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=cleaned_text,
                        char_count=char_count,
                        is_empty=(char_count == 0),
                        headings=headings,
                        tables=tables,
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
