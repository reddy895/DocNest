from datetime import datetime, timezone
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.database import get_db
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import UserOut
from backend.app.models.settings import UserSettingsModel, PresetApplyRequest, RAG_PRESETS

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=UserSettingsModel)
async def get_user_settings(
    current_user: UserOut = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Retrieve persisted RAG pipeline configuration for current user."""
    cursor = await db.execute(
        """
        SELECT chunk_size, chunk_overlap, top_k, min_relevance_score, temperature,
               hybrid_enabled, reranker_enabled, preset_name, updated_at
        FROM user_settings WHERE user_id = ?
        """,
        (current_user.id,),
    )
    row = await cursor.fetchone()
    if not row:
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """
            INSERT OR IGNORE INTO user_settings (user_id, chunk_size, chunk_overlap, top_k, min_relevance_score, temperature, hybrid_enabled, reranker_enabled, preset_name, updated_at)
            VALUES (?, 512, 64, 5, 0.30, 0.1, 1, 1, 'balanced', ?)
            """,
            (current_user.id, now_iso),
        )
        await db.commit()
        return UserSettingsModel(updated_at=now_iso)

    return UserSettingsModel(
        chunk_size=row["chunk_size"],
        chunk_overlap=row["chunk_overlap"],
        top_k=row["top_k"],
        min_relevance_score=row["min_relevance_score"],
        temperature=row["temperature"],
        hybrid_enabled=bool(row["hybrid_enabled"]),
        reranker_enabled=bool(row["reranker_enabled"]),
        preset_name=row["preset_name"],
        updated_at=row["updated_at"],
    )


@router.put("", response_model=UserSettingsModel)
async def update_user_settings(
    settings_in: UserSettingsModel,
    current_user: UserOut = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update custom RAG pipeline parameters."""
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """
        INSERT INTO user_settings (user_id, chunk_size, chunk_overlap, top_k, min_relevance_score, temperature, hybrid_enabled, reranker_enabled, preset_name, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            chunk_size=excluded.chunk_size,
            chunk_overlap=excluded.chunk_overlap,
            top_k=excluded.top_k,
            min_relevance_score=excluded.min_relevance_score,
            temperature=excluded.temperature,
            hybrid_enabled=excluded.hybrid_enabled,
            reranker_enabled=excluded.reranker_enabled,
            preset_name=excluded.preset_name,
            updated_at=excluded.updated_at
        """,
        (
            current_user.id,
            settings_in.chunk_size,
            settings_in.chunk_overlap,
            settings_in.top_k,
            settings_in.min_relevance_score,
            settings_in.temperature,
            1 if settings_in.hybrid_enabled else 0,
            1 if settings_in.reranker_enabled else 0,
            settings_in.preset_name,
            now_iso,
        ),
    )
    await db.commit()
    settings_in.updated_at = now_iso
    return settings_in


@router.post("/preset", response_model=UserSettingsModel)
async def apply_preset(
    req: PresetApplyRequest,
    current_user: UserOut = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Apply a 1-click RAG pipeline preset (strict, balanced, or deep)."""
    preset_data = RAG_PRESETS.get(req.preset_name)
    if not preset_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown preset '{req.preset_name}'. Choose from 'strict', 'balanced', 'deep'.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """
        INSERT INTO user_settings (user_id, chunk_size, chunk_overlap, top_k, min_relevance_score, temperature, hybrid_enabled, reranker_enabled, preset_name, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            chunk_size=excluded.chunk_size,
            chunk_overlap=excluded.chunk_overlap,
            top_k=excluded.top_k,
            min_relevance_score=excluded.min_relevance_score,
            temperature=excluded.temperature,
            hybrid_enabled=excluded.hybrid_enabled,
            reranker_enabled=excluded.reranker_enabled,
            preset_name=excluded.preset_name,
            updated_at=excluded.updated_at
        """,
        (
            current_user.id,
            preset_data["chunk_size"],
            preset_data["chunk_overlap"],
            preset_data["top_k"],
            preset_data["min_relevance_score"],
            preset_data["temperature"],
            1 if preset_data["hybrid_enabled"] else 0,
            1 if preset_data["reranker_enabled"] else 0,
            preset_data["preset_name"],
            now_iso,
        ),
    )
    await db.commit()

    return UserSettingsModel(
        chunk_size=preset_data["chunk_size"],
        chunk_overlap=preset_data["chunk_overlap"],
        top_k=preset_data["top_k"],
        min_relevance_score=preset_data["min_relevance_score"],
        temperature=preset_data["temperature"],
        hybrid_enabled=preset_data["hybrid_enabled"],
        reranker_enabled=preset_data["reranker_enabled"],
        preset_name=preset_data["preset_name"],
        updated_at=now_iso,
    )
