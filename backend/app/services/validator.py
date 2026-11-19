import hashlib
import re
from pathlib import Path
from typing import Tuple
from backend.app.core.config import settings
from backend.app.models.schemas import ValidationResult

PDF_MAGIC_BYTES = b"%PDF-"
DOCX_MAGIC_BYTES = b"PK\x03\x04"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for PDF documents specifically (legacy compatibility).
    """
    clean_name = Path(filename).name
    clean_name = re.sub(r"[^\w\.\- ]", "_", clean_name).strip()
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"
    return clean_name or "document.pdf"


def sanitize_document_filename(filename: str) -> str:
    """
    Sanitize filename preserving any allowed research document extension.
    """
    path = Path(filename)
    clean_stem = re.sub(r"[^\w\.\- ]", "_", path.stem).strip() or "document"
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".pdf"
    return f"{clean_stem}{ext}"


def compute_sha256(content: bytes) -> str:
    """
    Compute SHA-256 hash of file bytes for deduplication.
    """
    return hashlib.sha256(content).hexdigest()


def validate_pdf_content(filename: str, content: bytes) -> ValidationResult:
    """
    Validate uploaded PDF: check size limits, magic bytes, non-empty content, and structure.
    """
    clean_name = sanitize_filename(filename)
    file_size = len(content)
    file_hash = compute_sha256(content)

    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    # 1. Size checks
    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message="The uploaded file is empty (0 bytes).",
        )

    if file_size > max_size_bytes:
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # 2. Extension check
    if not clean_name.lower().endswith(".pdf"):
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message="Invalid file type. Only PDF documents are supported.",
        )

    # 3. Magic bytes verification (%PDF-)
    if not content.startswith(PDF_MAGIC_BYTES):
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message="Invalid PDF structure: Header magic bytes (%PDF-) not found.",
        )

    return ValidationResult(
        is_valid=True,
        filename=clean_name,
        file_size_bytes=file_size,
        file_hash=file_hash,
        error_message=None,
    )


def validate_document_file(filename: str, content: bytes) -> ValidationResult:
    """
    Validate any supported document format (PDF, DOCX, TXT, MD, CSV) with magic byte checks.
    """
    clean_name = sanitize_document_filename(filename)
    file_size = len(content)
    file_hash = compute_sha256(content)
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message="The uploaded file is empty (0 bytes).",
        )

    if file_size > max_size_bytes:
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )

    ext = Path(clean_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return ValidationResult(
            is_valid=False,
            filename=clean_name,
            file_size_bytes=file_size,
            file_hash=file_hash,
            error_message=f"Unsupported format '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Magic byte & content structure checks
    if ext == ".pdf":
        if not content.startswith(PDF_MAGIC_BYTES):
            return ValidationResult(
                is_valid=False,
                filename=clean_name,
                file_size_bytes=file_size,
                file_hash=file_hash,
                error_message="Invalid PDF structure: Header magic bytes (%PDF-) not found.",
            )
    elif ext == ".docx":
        if not content.startswith(DOCX_MAGIC_BYTES):
            return ValidationResult(
                is_valid=False,
                filename=clean_name,
                file_size_bytes=file_size,
                file_hash=file_hash,
                error_message="Invalid DOCX structure: ZIP header magic bytes not found.",
            )
    elif ext in [".txt", ".md", ".csv"]:
        # Verify valid text decodability
        try:
            content[:4096].decode("utf-8")
        except UnicodeDecodeError:
            try:
                content[:4096].decode("latin-1")
            except Exception:
                return ValidationResult(
                    is_valid=False,
                    filename=clean_name,
                    file_size_bytes=file_size,
                    file_hash=file_hash,
                    error_message=f"Corrupt or unreadable text in {ext.upper()} file.",
                )

    return ValidationResult(
        is_valid=True,
        filename=clean_name,
        file_size_bytes=file_size,
        file_hash=file_hash,
        error_message=None,
    )
