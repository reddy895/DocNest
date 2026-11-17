import hashlib
import re
from pathlib import Path
from typing import Tuple
from backend.app.core.config import settings
from backend.app.models.schemas import ValidationResult

PDF_MAGIC_BYTES = b"%PDF-"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and remove dangerous characters.
    """
    # Strip paths
    clean_name = Path(filename).name
    # Keep alphanumeric, dot, underscore, dash
    clean_name = re.sub(r"[^\w\.\- ]", "_", clean_name).strip()
    # Ensure it ends with .pdf
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"
    return clean_name or "document.pdf"


def compute_sha256(content: bytes) -> str:
    """
    Compute SHA-256 hash of file bytes for duplicate detection.
    """
    return hashlib.sha256(content).hexdigest()


def validate_pdf_content(filename: str, content: bytes) -> ValidationResult:
    """
    Validate uploaded file: check size limits, magic bytes, non-empty content, and structure.
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

