import logging
from typing import List, Optional
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import PlainTextResponse
from backend.app.core.database import get_db_connection
from backend.app.models.schemas import (
    SummarizeRequest,
    SummarizeResponse,
    CompareRequest,
    CompareResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    GenerateQuizRequest,
    GenerateQuizResponse,
    GenerateFlashcardsRequest,
    GenerateFlashcardsResponse,
    ResearchNoteCreateRequest,
    ResearchNoteUpdateRequest,
    ResearchNoteInfo,
)
from backend.app.services.research_service import get_research_service

logger = logging.getLogger("docnest.api.research")
router = APIRouter(prefix="/api/research", tags=["Research"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_documents(request: SummarizeRequest):
    """
    Generate grounded research summaries (executive, detailed, key_findings, or terms).
    """
    research_svc = get_research_service()
    try:
        result = await research_svc.summarize_documents(
            doc_ids=request.doc_ids,
            summary_type=request.summary_type,
            model=request.model,
        )
        return SummarizeResponse(**result)
    except Exception as exc:
        logger.error(f"Summarization error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(exc)}",
        )


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(request: CompareRequest):
    """
    Deep multi-document comparative analysis identifying agreements, contradictions, and comparison matrix.
    """
    if len(request.doc_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two document IDs must be provided for comparative analysis.",
        )
    research_svc = get_research_service()
    try:
        result = await research_svc.compare_documents(
            doc_ids=request.doc_ids,
            comparison_aspects=request.comparison_aspects,
            model=request.model,
        )
        return CompareResponse(**result)
    except Exception as exc:
        logger.error(f"Comparative analysis error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute comparative analysis: {str(exc)}",
        )


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate probing inquiry research questions grounded in document context.
    """
    research_svc = get_research_service()
    try:
        result = await research_svc.generate_questions(
            doc_ids=request.doc_ids,
            count=request.count,
            model=request.model,
        )
        return GenerateQuestionsResponse(**result)
    except Exception as exc:
        logger.error(f"Questions generation error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(exc)}",
        )


@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(request: GenerateQuizRequest):
    """
    Generate multiple choice questions with explanations and citations.
    """
    research_svc = get_research_service()
    try:
        result = await research_svc.generate_quiz(
            doc_ids=request.doc_ids,
            question_count=request.question_count,
            difficulty=request.difficulty,
            model=request.model,
        )
        return GenerateQuizResponse(**result)
    except Exception as exc:
        logger.error(f"Quiz generation error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(exc)}",
        )


@router.post("/generate-flashcards", response_model=GenerateFlashcardsResponse)
async def generate_flashcards(request: GenerateFlashcardsRequest):
    """
    Generate study flashcards for core definitions, concepts, and statistics.
    """
    research_svc = get_research_service()
    try:
        result = await research_svc.generate_flashcards(
            doc_ids=request.doc_ids,
            card_count=request.card_count,
            model=request.model,
        )
        return GenerateFlashcardsResponse(**result)
    except Exception as exc:
        logger.error(f"Flashcards generation error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(exc)}",
        )


# --- Research Notes Endpoints ---

@router.get("/notes", response_model=List[ResearchNoteInfo])
async def list_research_notes(session_id: Optional[str] = None):
    """List persistent research notes, optionally filtered by session_id."""
    async with get_db_connection() as db:
        if session_id:
            cursor = await db.execute(
                """
                SELECT id, user_id, session_id, title, content, tags, source_references, created_at, updated_at
                FROM research_notes
                WHERE session_id = ?
                ORDER BY updated_at DESC
                """,
                (session_id,),
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, user_id, session_id, title, content, tags, source_references, created_at, updated_at
                FROM research_notes
                ORDER BY updated_at DESC
                """
            )
        rows = await cursor.fetchall()

    notes = []
    for r in rows:
        nid, uid, sid, title, content, tags_json, cites_json, cat, uat = r
        notes.append(
            ResearchNoteInfo(
                id=nid,
                user_id=uid,
                session_id=sid,
                title=title,
                content=content,
                tags=json.loads(tags_json or "[]"),
                source_citations=json.loads(cites_json or "[]"),
                created_at=cat,
                updated_at=uat,
            )
        )
    return notes


@router.post("/notes", response_model=ResearchNoteInfo, status_code=status.HTTP_201_CREATED)
async def create_research_note(request: ResearchNoteCreateRequest):
    """Save a new research note with citations and tags."""
    note_id = f"note_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    tags_str = json.dumps(request.tags)
    cites_str = json.dumps(request.source_citations)

    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO research_notes (id, user_id, workspace_id, session_id, title, content, tags, source_references, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_id,
                "user_default_local",
                "Default Workspace",
                request.session_id,
                request.title,
                request.content,
                tags_str,
                cites_str,
                now_iso,
                now_iso,
            ),
        )
        await db.commit()

    return ResearchNoteInfo(
        id=note_id,
        user_id="user_default_local",
        session_id=request.session_id,
        title=request.title,
        content=request.content,
        tags=request.tags,
        source_citations=request.source_citations,
        created_at=now_iso,
        updated_at=now_iso,
    )


@router.patch("/notes/{note_id}", response_model=ResearchNoteInfo)
async def update_research_note(note_id: str, request: ResearchNoteUpdateRequest):
    """Update title, content, or tags of an existing research note."""
    now_iso = datetime.now(timezone.utc).isoformat()
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM research_notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Research note not found")

        updates = ["updated_at = ?"]
        params = [now_iso]

        if request.title is not None:
            updates.append("title = ?")
            params.append(request.title)
        if request.content is not None:
            updates.append("content = ?")
            params.append(request.content)
        if request.tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(request.tags))

        params.append(note_id)
        await db.execute(f"UPDATE research_notes SET {', '.join(updates)} WHERE id = ?", tuple(params))
        await db.commit()

        cursor = await db.execute(
            """
            SELECT id, user_id, session_id, title, content, tags, source_references, created_at, updated_at
            FROM research_notes WHERE id = ?
            """,
            (note_id,),
        )
        updated_row = await cursor.fetchone()

    nid, uid, sid, title, content, tags_json, cites_json, cat, uat = updated_row
    return ResearchNoteInfo(
        id=nid,
        user_id=uid,
        session_id=sid,
        title=title,
        content=content,
        tags=json.loads(tags_json or "[]"),
        source_citations=json.loads(cites_json or "[]"),
        created_at=cat,
        updated_at=uat,
    )


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_note(note_id: str):
    """Delete a research note."""
    async with get_db_connection() as db:
        cursor = await db.execute("DELETE FROM research_notes WHERE id = ?", (note_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Research note not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notes/{note_id}/export")
async def export_research_note_markdown(note_id: str):
    """Export a research note as a clean GitHub-flavored Markdown document."""
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT title, content, tags, source_references, created_at FROM research_notes WHERE id = ?",
            (note_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Research note not found")

    title, content, tags_json, cites_json, cat = row
    tags = json.loads(tags_json or "[]")
    citations = json.loads(cites_json or "[]")

    lines = [
        f"# {title}",
        f"*Created on {cat} | DocNest Research Workspace*",
        "",
    ]
    if tags:
        lines.append(f"**Tags**: {', '.join(tags)}")
        lines.append("")

    lines.append("## Notes & Synthesis")
    lines.append(content)
    lines.append("")

    if citations:
        lines.append("## Referenced Sources")
        for cite in citations:
            fname = cite.get("filename", "Document")
            pnum = cite.get("page_number", 1)
            lines.append(f"- **{fname}** (Page {pnum})")
        lines.append("")

    md_text = "\n".join(lines)
    filename = f"{title.lower().replace(' ', '_')[:32]}.md"
    return PlainTextResponse(
        content=md_text,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
