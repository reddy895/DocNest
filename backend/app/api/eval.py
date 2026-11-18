import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite
from backend.app.core.database import get_db
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import UserOut

logger = logging.getLogger("docnest.api.eval")
router = APIRouter(prefix="/api/eval", tags=["Evaluation"])


@router.get("/runs")
async def list_eval_runs(
    current_user: UserOut = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """List historical RAG evaluation benchmark runs for current workspace."""
    cursor = await db.execute(
        """
        SELECT id, faithfulness_score, relevancy_score, precision_score,
               avg_retrieval_ms, avg_ttft_ms, total_questions, created_at
        FROM eval_runs
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (current_user.id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
