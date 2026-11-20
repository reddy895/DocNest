import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse

from backend.app.services.sample_generator import generate_sample_pdfs, settings as sample_settings
from backend.app.services.validator import validate_document_file, validate_pdf_content, compute_sha256
from backend.app.services.pdf_extractor import extract_pdf_pages, extract_document_content
from backend.app.services.chunker import create_document_chunks
from backend.app.services.chroma_service import get_chroma_service
from backend.app.services.ingestion_queue import process_document_ingestion
from backend.app.models.document import DocumentRecord
from backend.app.models.schemas import (
    DocumentInfo,
    DocumentListResponse,
    DeleteDocumentResponse,
    DocumentStatusResponse,
    DocumentUpdateRequest,
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionInfo,
)
from backend.app.core.config import settings
from backend.app.core.database import get_db_connection

logger = logging.getLogger("docnest.api.documents")
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/load-sample", response_model=List[DocumentInfo])
async def load_sample_documents(
    sample_type: str = Query("all", description="Sample key: financial, ai_whitepaper, compliance, or all")
):
    """
    One-click onboarding: Load, parse, chunk, and index curated enterprise sample PDFs.
    """
    generate_sample_pdfs()
    sample_files = {
        "financial": ("quarterly_financial_report.pdf", "Quarterly Financial Report Q3.pdf"),
        "ai_whitepaper": ("ai_architecture_whitepaper.pdf", "Enterprise AI Architecture Whitepaper.pdf"),
        "compliance": ("compliance_policy_manual.pdf", "Corporate Compliance Policy Manual.pdf"),
    }

    targets = []
    if sample_type == "all":
        targets = list(sample_files.values())
    elif sample_type in sample_files:
        targets = [sample_files[sample_type]]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown sample type '{sample_type}'. Valid choices: {list(sample_files.keys())} or 'all'",
        )

    results: List[DocumentInfo] = []
    chroma = get_chroma_service()

    for disk_name, display_name in targets:
        pdf_path = settings.SAMPLES_DIR / disk_name
        if not pdf_path.exists():
            continue

        with open(pdf_path, "rb") as f:
            content = f.read()

        file_hash = compute_sha256(content)
        existing_doc = chroma.find_document_by_hash(file_hash)
        if existing_doc:
            results.append(
                DocumentInfo(
                    doc_id=existing_doc.doc_id,
                    filename=existing_doc.filename,
                    file_size_bytes=existing_doc.file_size_bytes,
                    file_hash=existing_doc.file_hash,
                    page_count=existing_doc.page_count,
                    total_chunks=existing_doc.total_chunks,
                    upload_date=existing_doc.upload_date,
                    status="ready",
                    progress_pct=100,
                    is_scanned=existing_doc.is_scanned,
                )
            )
            continue

        doc_id = f"sample_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        dest_path = settings.DOCUMENTS_DIR / f"{doc_id}.pdf"
        with open(dest_path, "wb") as f:
            f.write(content)

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
                    display_name,
                    file_hash,
                    len(content),
                    1,
                    1,
                    "ready",
                    100,
                    "",
                    0,
                    '["sample"]',
                    str(dest_path),
                    now_iso,
                    now_iso,
                ),
            )
            await db.commit()

        await process_document_ingestion(
            doc_id=doc_id,
            file_bytes=content,
            filename=display_name,
            file_hash=file_hash,
            user_id="user_default_local",
            workspace_id="Default Workspace",
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        doc_rec = chroma.find_document_by_id(doc_id)
        results.append(
            DocumentInfo(
                doc_id=doc_id,
                filename=display_name,
                file_size_bytes=len(content),
                file_hash=file_hash,
                page_count=doc_rec.page_count if doc_rec else 1,
                total_chunks=doc_rec.total_chunks if doc_rec else 1,
                upload_date=now_iso,
                status="ready",
                progress_pct=100,
                is_scanned=False,
                tags=["sample"],
            )
        )

    return results


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


@router.patch("/{doc_id}", response_model=DocumentInfo)
async def update_document_metadata(doc_id: str, payload: DocumentUpdateRequest):
    """
    Update document filename, tags, or assigned workspace.
    """
    import json
    chroma = get_chroma_service()
    doc = chroma.find_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    new_filename = payload.filename or doc.filename
    new_tags = payload.tags if payload.tags is not None else []

    async with get_db_connection() as db:
        await db.execute(
            """
            UPDATE documents
            SET filename = ?, tags = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_filename, json.dumps(new_tags), now_iso, doc_id),
        )
        await db.commit()

    doc.filename = new_filename
    chroma._save_registry(chroma._load_registry())

    return DocumentInfo(
        doc_id=doc.doc_id,
        filename=new_filename,
        file_size_bytes=doc.file_size_bytes,
        file_hash=doc.file_hash,
        page_count=doc.page_count,
        total_chunks=doc.total_chunks,
        upload_date=doc.upload_date,
        status="ready",
        progress_pct=100,
        is_scanned=doc.is_scanned,
        tags=new_tags,
    )


@router.post("/{doc_id}/reindex", response_model=DocumentStatusResponse)
async def reindex_document(doc_id: str, background_tasks: BackgroundTasks):
    """
    Re-extract and re-embed document with updated chunking settings.
    """
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = row["file_path"]
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=400, detail="Document file missing from disk")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE documents SET status = 'queued', progress_pct = 0, error_msg = '', updated_at = ? WHERE id = ?",
            (now_iso, doc_id),
        )
        await db.commit()

        # Delete existing chunks first
        chroma = get_chroma_service()
        chroma.delete_document(doc_id)

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


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document(doc_id: str):
    """
    Cascade delete: Remove document from SQLite, ChromaDB vectors, and local disk.
    """
    chroma = get_chroma_service()
    doc = chroma.find_document_by_id(doc_id)

    # 1. Cascade delete in SQLite
    async with get_db_connection() as db:
        await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await db.commit()

    if not doc:
        return DeleteDocumentResponse(
            doc_id=doc_id,
            filename="unknown",
            chunks_deleted=0,
            success=True,
            message="Document removed from database.",
        )

    # 2. Delete vectors and files via ChromaService
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
    workspace_id: Optional[str] = Query("Default Workspace", description="Target research workspace"),
    async_processing: bool = Query(False, description="Run ingestion asynchronously in background queue"),
):
    """
    Upload, validate, extract, chunk, and index any supported document (PDF, DOCX, TXT, MD, CSV).
    Enforces format validation, deduplication, SQLite recording, and page-by-page metadata.
    """
    filename = file.filename or "document.pdf"
    content = await file.read()

    # 1. Multi-format Validation
    validation = validate_document_file(filename, content)
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
    ext = Path(validation.filename).suffix.lower() or ".pdf"
    file_path = settings.DOCUMENTS_DIR / f"{doc_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    ws_id = workspace_id or "Default Workspace"

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
                ws_id,
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
            workspace_id=ws_id,
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
        workspace_id=ws_id,
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


@router.post("/batch-upload", response_model=List[DocumentInfo], status_code=status.HTTP_201_CREATED)
async def batch_upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    workspace_id: Optional[str] = Query("Default Workspace"),
    async_processing: bool = Query(True),
):
    """
    Multi-file concurrent document upload endpoint. Validates, records, and enqueues
    multiple documents for asynchronous background processing.
    """
    chroma = get_chroma_service()
    ws_id = workspace_id or "Default Workspace"
    uploaded_records: List[DocumentInfo] = []

    for file in files:
        filename = file.filename or "document.pdf"
        content = await file.read()

        validation = validate_document_file(filename, content)
        if not validation.is_valid:
            continue

        existing_doc = chroma.find_document_by_hash(validation.file_hash)
        if existing_doc:
            uploaded_records.append(
                DocumentInfo(
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
            )
            continue

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        ext = Path(validation.filename).suffix.lower() or ".pdf"
        file_path = settings.DOCUMENTS_DIR / f"{doc_id}{ext}"
        with open(file_path, "wb") as f:
            f.write(content)

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
                    ws_id,
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
                workspace_id=ws_id,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            uploaded_records.append(
                DocumentInfo(
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
            )
        else:
            await process_document_ingestion(
                doc_id=doc_id,
                file_bytes=content,
                filename=validation.filename,
                file_hash=validation.file_hash,
                user_id="user_default_local",
                workspace_id=ws_id,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            doc_record = chroma.find_document_by_id(doc_id)
            uploaded_records.append(
                DocumentInfo(
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
            )

    return uploaded_records


# ---------------- COLLECTIONS MANAGEMENT ----------------

@router.get("/collections", response_model=List[CollectionInfo])
async def list_document_collections():
    """List all research document collections / binders."""
    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, workspace_id, name, description, color, document_ids, created_at, updated_at
            FROM document_collections
            ORDER BY updated_at DESC
            """
        )
        rows = await cursor.fetchall()
        collections = []
        for r in rows:
            try:
                doc_ids = json.loads(r["document_ids"])
            except Exception:
                doc_ids = []
            collections.append(
                CollectionInfo(
                    id=r["id"],
                    user_id=r["user_id"],
                    workspace_id=r["workspace_id"],
                    name=r["name"],
                    description=r["description"] or "",
                    color=r["color"] or "#E5B83D",
                    document_ids=doc_ids,
                    document_count=len(doc_ids),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return collections


@router.post("/collections", response_model=CollectionInfo, status_code=status.HTTP_201_CREATED)
async def create_document_collection(payload: CollectionCreateRequest):
    """Create a new research collection / binder."""
    col_id = f"col_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    doc_ids_json = json.dumps(payload.document_ids or [])

    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO document_collections (
                id, user_id, workspace_id, name, description, color, document_ids, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                col_id,
                "user_default_local",
                "Default Workspace",
                payload.name.strip(),
                payload.description or "",
                payload.color or "#E5B83D",
                doc_ids_json,
                now_iso,
                now_iso,
            ),
        )
        await db.commit()

    return CollectionInfo(
        id=col_id,
        user_id="user_default_local",
        workspace_id="Default Workspace",
        name=payload.name.strip(),
        description=payload.description or "",
        color=payload.color or "#E5B83D",
        document_ids=payload.document_ids or [],
        document_count=len(payload.document_ids or []),
        created_at=now_iso,
        updated_at=now_iso,
    )


@router.patch("/collections/{col_id}", response_model=CollectionInfo)
async def update_document_collection(col_id: str, payload: CollectionUpdateRequest):
    """Update name, description, color or document membership of a collection."""
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM document_collections WHERE id = ?", (col_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Collection not found")

        updates = []
        params = []
        now_iso = datetime.now(timezone.utc).isoformat()

        if payload.name is not None:
            updates.append("name = ?")
            params.append(payload.name.strip())
        if payload.description is not None:
            updates.append("description = ?")
            params.append(payload.description)
        if payload.color is not None:
            updates.append("color = ?")
            params.append(payload.color)
        if payload.document_ids is not None:
            updates.append("document_ids = ?")
            params.append(json.dumps(payload.document_ids))

        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(col_id)

        query = f"UPDATE document_collections SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, tuple(params))
        await db.commit()

        cursor = await db.execute("SELECT * FROM document_collections WHERE id = ?", (col_id,))
        updated = await cursor.fetchone()
        try:
            doc_ids = json.loads(updated["document_ids"])
        except Exception:
            doc_ids = []

        return CollectionInfo(
            id=updated["id"],
            user_id=updated["user_id"],
            workspace_id=updated["workspace_id"],
            name=updated["name"],
            description=updated["description"] or "",
            color=updated["color"] or "#E5B83D",
            document_ids=doc_ids,
            document_count=len(doc_ids),
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
        )


@router.delete("/collections/{col_id}")
async def delete_document_collection(col_id: str):
    """Delete a research collection."""
    async with get_db_connection() as db:
        await db.execute("DELETE FROM document_collections WHERE id = ?", (col_id,))
        await db.commit()
    return {"success": True, "collection_id": col_id, "message": "Collection deleted successfully"}
