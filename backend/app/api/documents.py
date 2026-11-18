import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse

from backend.app.services.validator import validate_pdf_content
from backend.app.services.pdf_extractor import extract_pdf_pages
from backend.app.services.chunker import create_document_chunks
from backend.app.services.chroma_service import get_chroma_service
from backend.app.services.ingestion_queue import process_document_ingestion
from backend.app.models.document import DocumentRecord
from backend.app.models.schemas import (
    DocumentInfo,
    DocumentListResponse,
    DeleteDocumentResponse,
    DocumentStatusResponse,
)
from backend.app.core.config import settings
from backend.app.core.database import get_db_connection

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


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str):
    """
    Get real-time ingestion status and progress for polling or SSE sync.
    """
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT id, filename, status, progress_pct, error_msg, page_count, total_chunks, is_scanned, updated_at
            FROM documents WHERE id = ?
            """,
            (doc_id,),
        )
        row = await cursor.fetchone()
        if not row:
            # Check Chroma registry as fallback
            chroma = get_chroma_service()
            doc = chroma.find_document_by_id(doc_id)
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found.",
                )
            return DocumentStatusResponse(
                doc_id=doc.doc_id,
                filename=doc.filename,
                status="ready",
                progress_pct=100,
                error_msg=None,
                page_count=doc.page_count,
                total_chunks=doc.total_chunks,
                is_scanned=doc.is_scanned,
                updated_at=doc.upload_date,
            )

        return DocumentStatusResponse(
            doc_id=row["id"],
            filename=row["filename"],
            status=row["status"],
            progress_pct=row["progress_pct"],
            error_msg=row["error_msg"],
            page_count=row["page_count"],
            total_chunks=row["total_chunks"],
            is_scanned=bool(row["is_scanned"]),
            updated_at=row["updated_at"],
        )


@router.post("/{doc_id}/retry", response_model=DocumentStatusResponse)
async def retry_document_ingestion(doc_id: str, background_tasks: BackgroundTasks):
    """
    Retry processing for a failed document ingestion.
    """
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = row["file_path"]
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=400, detail="Original document file missing from disk")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE documents SET status = 'queued', progress_pct = 0, error_msg = '', updated_at = ? WHERE id = ?",
            (now_iso, doc_id),
        )
        await db.commit()

        background_tasks.add_task(
            process_document_ingestion,
            doc_id=doc_id,
            file_bytes=file_bytes,
            filename=row["filename"],
            file_hash=row["file_hash"],
            user_id=row["user_id"],
            workspace_id=row["workspace_id"],
        )

        return DocumentStatusResponse(
            doc_id=doc_id,
            filename=row["filename"],
            status="queued",
            progress_pct=0,
            error_msg=None,
            page_count=row["page_count"],
            total_chunks=row["total_chunks"],
            is_scanned=bool(row["is_scanned"]),
            updated_at=now_iso,
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


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document(doc_id: str):
    """
    Delete a document, purges its chunks from ChromaDB, and removes file from disk.
    """
    chroma = get_chroma_service()
    doc = chroma.find_document_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found.",
        )

    deleted_count = chroma.delete_document(doc_id)

    return DeleteDocumentResponse(
        doc_id=doc_id,
        filename=doc.filename,
        chunks_deleted=deleted_count,
        success=True,
        message=f"Document '{doc.filename}' and {deleted_count} chunks deleted successfully.",
    )


@router.post("/upload", response_model=DocumentInfo, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    async_processing: bool = Query(False, description="Run ingestion asynchronously in background queue"),
):
    """
    Upload, validate, extract, chunk, and index a PDF document.
    Enforces magic bytes verification, deduplication, SQLite recording, and page-by-page metadata.
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
            progress_pct=100,
            is_scanned=existing_doc.is_scanned,
        )

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    file_path = settings.DOCUMENTS_DIR / f"{doc_id}.pdf"
    with open(file_path, "wb") as f:
        f.write(content)

    # Insert initial entry into SQLite
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO documents (
                id, user_id, workspace_id, filename, file_hash, file_size_bytes,
                page_count, total_chunks, status, progress_pct, error_msg, is_scanned,
                tags, file_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                "user_default_local",
                "Default Workspace",
                validation.filename,
                validation.file_hash,
                validation.file_size_bytes,
                0,
                0,
                "queued" if async_processing else "parsing",
                0 if async_processing else 25,
                "",
                0,
                "[]",
                str(file_path),
                now_iso,
                now_iso,
            ),
        )
        await db.commit()

    if async_processing:
        background_tasks.add_task(
            process_document_ingestion,
            doc_id=doc_id,
            file_bytes=content,
            filename=validation.filename,
            file_hash=validation.file_hash,
            user_id="user_default_local",
            workspace_id="Default Workspace",
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        return DocumentInfo(
            doc_id=doc_id,
            filename=validation.filename,
            file_size_bytes=validation.file_size_bytes,
            file_hash=validation.file_hash,
            page_count=0,
            total_chunks=0,
            upload_date=now_iso,
            status="queued",
            progress_pct=0,
            is_scanned=False,
        )

    # Synchronous processing
    await process_document_ingestion(
        doc_id=doc_id,
        file_bytes=content,
        filename=validation.filename,
        file_hash=validation.file_hash,
        user_id="user_default_local",
        workspace_id="Default Workspace",
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    doc_record = chroma.find_document_by_id(doc_id)
    return DocumentInfo(
        doc_id=doc_id,
        filename=validation.filename,
        file_size_bytes=validation.file_size_bytes,
        file_hash=validation.file_hash,
        page_count=doc_record.page_count if doc_record else 1,
        total_chunks=doc_record.total_chunks if doc_record else 1,
        upload_date=now_iso,
        status="ready",
        progress_pct=100,
        is_scanned=doc_record.is_scanned if doc_record else False,
    )
