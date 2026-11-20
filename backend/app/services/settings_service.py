import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from backend.app.core.database import get_db_connection
from backend.app.core.mongo import get_mongo_db
from backend.app.models.settings import UserSettingsModel, RAG_PRESETS

logger = logging.getLogger("docnest.settings")


class SettingsService:
    """
    Manages persistence of user-specific and system-wide RAG parameters
    with SQLite and MongoDB dual-layer synchronization.
    """

    async def get_user_settings(self, user_id: str) -> UserSettingsModel:
        """Fetch user settings, auto-initializing with default balanced preset if missing."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT chunk_size, chunk_overlap, top_k, min_relevance_score, temperature,
                       hybrid_enabled, reranker_enabled, preset_name, updated_at
                FROM user_settings WHERE user_id = ?
                """,
                (user_id,),
            )
            row = await cursor.fetchone()
            if not row:
                now_iso = datetime.now(timezone.utc).isoformat()
                await db.execute(
                    """
                    INSERT OR IGNORE INTO user_settings (
                        user_id, chunk_size, chunk_overlap, top_k, min_relevance_score,
                        temperature, hybrid_enabled, reranker_enabled, preset_name, updated_at
                    )
                    VALUES (?, 512, 64, 5, 0.30, 0.1, 1, 1, 'balanced', ?)
                    """,
                    (user_id, now_iso),
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

    async def update_user_settings(self, user_id: str, settings: UserSettingsModel) -> UserSettingsModel:
        """Upsert user settings to SQLite and MongoDB."""
        now_iso = datetime.now(timezone.utc).isoformat()
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO user_settings (
                    user_id, chunk_size, chunk_overlap, top_k, min_relevance_score,
                    temperature, hybrid_enabled, reranker_enabled, preset_name, updated_at
                )
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
                    user_id,
                    settings.chunk_size,
                    settings.chunk_overlap,
                    settings.top_k,
                    settings.min_relevance_score,
                    settings.temperature,
                    1 if settings.hybrid_enabled else 0,
                    1 if settings.reranker_enabled else 0,
                    settings.preset_name,
                    now_iso,
                ),
            )
            await db.commit()

        # Sync to MongoDB if available
        mongo = get_mongo_db()
        if mongo:
            try:
                await mongo.user_settings.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "user_id": user_id,
                        "chunk_size": settings.chunk_size,
                        "chunk_overlap": settings.chunk_overlap,
                        "top_k": settings.top_k,
                        "min_relevance_score": settings.min_relevance_score,
                        "temperature": settings.temperature,
                        "hybrid_enabled": settings.hybrid_enabled,
                        "reranker_enabled": settings.reranker_enabled,
                        "preset_name": settings.preset_name,
                        "updated_at": now_iso,
                    }},
                    upsert=True,
                )
            except Exception as e:
                logger.debug(f"MongoDB settings sync deferred: {e}")

        settings.updated_at = now_iso
        return settings

    async def apply_preset(self, user_id: str, preset_name: str) -> UserSettingsModel:
        """Apply predefined configuration preset."""
        preset_data = RAG_PRESETS.get(preset_name)
        if not preset_data:
            raise ValueError(f"Unknown preset '{preset_name}'. Valid presets: {list(RAG_PRESETS.keys())}")

        current = await self.get_user_settings(user_id)
        for key, val in preset_data.items():
            setattr(current, key, val)
        current.preset_name = preset_name
        return await self.update_user_settings(user_id, current)


_settings_service: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
