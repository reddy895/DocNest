import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.database import get_db_connection
from backend.app.models.document import DocumentRecord
from backend.app.services.pdf_extractor import extract_pdf_pages
from backend.app.services.chunker import create_document_chunks
from backend.app.services.chroma_service import get_chroma_service

logger = logging.getLogger("docnest.queue")


async def update_job_status(
    doc_id: str,
    status: str,
    progress_pct: int,
    error_msg: Optional[str] = None,
    page_count: Optional[int] = None,
    total_chunks: Optional[int] = None,
    is_scanned: Optional[bool] = None,
) -> None:
    """Update ingestion job status in SQLite asynchronously."""
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        async with get_db_connection() as db:
            updates = ["status = ?", "progress_pct = ?", "updated_at = ?"]
            params = [status, progress_pct, now_iso]

            if error_msg is not None:
                updates.append("error_msg = ?")
                params.append(error_msg)
            if page_count is not None:
                updates.append("page_count = ?")
                params.append(page_count)
            if total_chunks is not None:
                updates.append("total_chunks = ?")
                params.append(total_chunks)
            if is_scanned is not None:
                updates.append("is_scanned = ?")
                params.append(1 if is_scanned else 0)

            params.append(doc_id)
            query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, tuple(params))
            await db.commit()
    except Exception as exc:
        logger.error(f"Failed to update job status for doc {doc_id}: {exc}")


async def process_document_ingestion(
    doc_id: str,
    file_bytes: bytes,
    filename: str,
    file_hash: str,
    user_id: str,
    workspace_id: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> None:
    """
    Background worker pipeline executing granular stages:
    queued -> parsing -> chunking -> embedding -> ready
    """
    logger.info(f"Starting ingestion pipeline for doc_id={doc_id} ('{filename}')")

    try:
        # Stage 1: Parsing
        await update_job_status(doc_id, status="parsing", progress_pct=25)
        # Run parsing in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        extraction_result = await loop.run_in_executor(
            None, extract_pdf_pages, file_bytes, filename
        )

        if extraction_result.error_message:
            await update_job_status(
                doc_id,
                status="failed",
                progress_pct=25,
                error_msg=extraction_result.error_message,
            )
            return

        page_count = extraction_result.page_count
        is_scanned = extraction_result.is_scanned

        # Stage 2: Chunking
        await update_job_status(
            doc_id,
            status="chunking",
            progress_pct=50,
            page_count=page_count,
            is_scanned=is_scanned,
        )

        chunks = await loop.run_in_executor(
            None,
            create_document_chunks,
            doc_id,
            filename,
            file_hash,
            extraction_result.pages,
            chunk_size,
            chunk_overlap,
            user_id,
            workspace_id,
        )

        total_chunks = len(chunks)

        # Stage 3: Embedding & Vector Storage
        await update_job_status(
            doc_id,
            status="embedding",
            progress_pct=75,
            total_chunks=total_chunks,
        )

        chroma_svc = get_chroma_service()

        doc_record = DocumentRecord(
            doc_id=doc_id,
            filename=filename,
            file_hash=file_hash,
            file_size_bytes=len(file_bytes),
            page_count=page_count,
            total_chunks=total_chunks,
            is_scanned=is_scanned,
        )

        await loop.run_in_executor(
            None,
            chroma_svc.save_document,
            doc_record,
            file_bytes,
            chunks,
        )

        # Stage 4: Ready
        await update_job_status(
            doc_id,
            status="ready",
            progress_pct=100,
            error_msg="",
            page_count=page_count,
            total_chunks=total_chunks,
        )
        logger.info(f"Ingestion pipeline completed successfully for doc_id={doc_id} ('{filename}')")

    except Exception as exc:
        logger.error(f"Ingestion pipeline encountered fatal error for doc_id={doc_id}: {exc}", exc_info=True)
        await update_job_status(
            doc_id,
            status="failed",
            progress_pct=100,
            error_msg=f"Processing failed: {str(exc)}",
        )
