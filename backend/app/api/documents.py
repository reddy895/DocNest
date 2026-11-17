import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from backend.app.services.validator import validate_pdf_content
from backend.app.services.pdf_extractor import extract_pdf_pages
from backend.app.services.chunker import create_document_chunks
from backend.app.services.chroma_service import get_chroma_service
from backend.app.models.document import DocumentRecord
from backend.app.models.schemas import DocumentInfo, DocumentListResponse
from backend.app.core.config import settings

logger = logging.getLogger("docnest.api.documents")
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """
    List all uploaded and indexed documents with global repository statistics.
    """
    chroma = get_chroma_service()
    doc_records = chroma.list_documents()

    doc_infos = [
        DocumentInfo(
            doc_id=d.doc_id,
            filename=d.filename,
            file_size_bytes=d.file_size_bytes,
            file_hash=d.file_hash,
            page_count=d.page_count,
            total_chunks=d.total_chunks,
            upload_date=d.upload_date,
            status=d.status,
            is_scanned=d.is_scanned,
        )
        for d in doc_records
    ]

    total_chunks = chroma.count()

    return DocumentListResponse(
        total_documents=len(doc_infos),
        total_chunks=total_chunks,
        documents=doc_infos,
    )


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(doc_id: str):
    """
    Retrieve metadata for a specific document by its ID.
    """
    chroma = get_chroma_service()
    doc = chroma.find_document_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found.",
        )

    return DocumentInfo(
        doc_id=doc.doc_id,
        filename=doc.filename,
        file_size_bytes=doc.file_size_bytes,
        file_hash=doc.file_hash,
        page_count=doc.page_count,
        total_chunks=doc.total_chunks,
        upload_date=doc.upload_date,
        status=doc.status,
        is_scanned=doc.is_scanned,
    )


@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str):
    """
    Serve raw PDF binary file for embedded preview or direct download.
    """
    chroma = get_chroma_service()
    doc = chroma.find_document_by_id(doc_id)
    if not doc or not doc.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document file for ID '{doc_id}' not found on disk.",
        )

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file missing from storage directory.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc.filename,
    )


@router.post("/upload", response_model=DocumentInfo, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload, validate, extract, chunk, and index a PDF document.
    Enforces magic bytes verification, deduplication, and page-by-page metadata.
    """
    filename = file.filename or "document.pdf"
    content = await file.read()

    # 1. Validation
    validation = validate_pdf_content(filename, content)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.error_message,
        )

    chroma = get_chroma_service()

    # 2. Duplicate Detection
    existing_doc = chroma.find_document_by_hash(validation.file_hash)
    if existing_doc:
        logger.info(f"Duplicate document detected: '{validation.filename}' matches '{existing_doc.filename}'")
        return DocumentInfo(
            doc_id=existing_doc.doc_id,
            filename=existing_doc.filename,
            file_size_bytes=existing_doc.file_size_bytes,
            file_hash=existing_doc.file_hash,
            page_count=existing_doc.page_count,
            total_chunks=existing_doc.total_chunks,
            upload_date=existing_doc.upload_date,
            status="already_indexed",
            is_scanned=existing_doc.is_scanned,
        )

    # 3. Text Extraction
    extraction = extract_pdf_pages(content, validation.filename)
    if extraction.error_message or extraction.page_count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=extraction.error_message or "Failed to extract readable content from PDF.",
        )

    # 4. Semantic Chunking
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    chunks = create_document_chunks(
        doc_id=doc_id,
        filename=validation.filename,
        file_hash=validation.file_hash,
        pages=extraction.pages,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    # 5. Persistent Storage & Indexing
    doc_record = DocumentRecord(
        doc_id=doc_id,
        filename=validation.filename,
        file_hash=validation.file_hash,
        file_size_bytes=validation.file_size_bytes,
        page_count=extraction.page_count,
        total_chunks=len(chunks),
        is_scanned=extraction.is_scanned,
        status="indexed",
    )

    chroma.save_document(doc_record, content, chunks)

    return DocumentInfo(
        doc_id=doc_record.doc_id,
        filename=doc_record.filename,
        file_size_bytes=doc_record.file_size_bytes,
        file_hash=doc_record.file_hash,
        page_count=doc_record.page_count,
        total_chunks=doc_record.total_chunks,
        upload_date=doc_record.upload_date,
        status="indexed",
        is_scanned=doc_record.is_scanned,
    )
