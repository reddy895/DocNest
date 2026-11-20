import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from backend.app.core.database import get_db_connection
from backend.app.core.mongo import get_mongo_db

logger = logging.getLogger("docnest.conversations")


class ConversationService:
    """
    High-performance persistence service for chat sessions and conversational messages
    supporting MongoDB and SQLite dual-layer storage with structured search and telemetry.
    """

    async def create_session(
        self,
        user_id: str,
        title: str = "New Research",
        workspace_id: str = "Default Workspace",
    ) -> Dict[str, Any]:
        """Create a new conversational research session."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        clean_title = title.strip() or "New Research"

        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO chat_sessions (id, user_id, workspace_id, title, is_pinned, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, ?)
                """,
                (session_id, user_id, workspace_id, clean_title, now_iso, now_iso),
            )
            await db.commit()

        # MongoDB dual-write
        mongo = get_mongo_db()
        if mongo:
            try:
                await mongo.chat_sessions.insert_one({
                    "id": session_id,
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "title": clean_title,
                    "is_pinned": False,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                })
            except Exception as e:
                logger.debug(f"MongoDB session sync deferred: {e}")

        return {
            "id": session_id,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "title": clean_title,
            "is_pinned": False,
            "created_at": now_iso,
            "updated_at": now_iso,
            "message_count": 0,
        }

    async def get_user_sessions(
        self,
        user_id: str,
        workspace_id: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch user sessions with message counts, optional search filter, and total count."""
        async with get_db_connection() as db:
            conditions = ["s.user_id = ?"]
            params: List[Any] = [user_id]

            if workspace_id and workspace_id != "all":
                conditions.append("s.workspace_id = ?")
                params.append(workspace_id)

            if search_query and search_query.strip():
                conditions.append("(s.title LIKE ? OR EXISTS (SELECT 1 FROM chat_messages m WHERE m.session_id = s.id AND m.text LIKE ?))")
                q_like = f"%{search_query.strip()}%"
                params.extend([q_like, q_like])

            where_clause = " AND ".join(conditions)

            # Total count
            cursor = await db.execute(f"SELECT COUNT(*) as total FROM chat_sessions s WHERE {where_clause}", tuple(params))
            total = (await cursor.fetchone())["total"]

            # Rows
            query = f"""
                SELECT s.id, s.user_id, s.workspace_id, s.title,
                       COALESCE(s.is_pinned, 0) as is_pinned,
                       s.created_at, s.updated_at,
                       COUNT(m.id) as msg_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.id = m.session_id
                WHERE {where_clause}
                GROUP BY s.id
                ORDER BY s.is_pinned DESC, s.updated_at DESC
                LIMIT ? OFFSET ?
            """
            cursor = await db.execute(query, tuple(params + [limit, offset]))
            rows = await cursor.fetchall()

            return [
                {
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "workspace_id": r["workspace_id"],
                    "title": r["title"],
                    "is_pinned": bool(r["is_pinned"]),
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "message_count": r["msg_count"],
                }
                for r in rows
            ], total

    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single session metadata."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT s.id, s.user_id, s.workspace_id, s.title,
                       COALESCE(s.is_pinned, 0) as is_pinned,
                       s.created_at, s.updated_at,
                       COUNT(m.id) as msg_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.id = m.session_id
                WHERE s.id = ?
                GROUP BY s.id
                """,
                (session_id,),
            )
            r = await cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "user_id": r["user_id"],
                "workspace_id": r["workspace_id"],
                "title": r["title"],
                "is_pinned": bool(r["is_pinned"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "message_count": r["msg_count"],
            }

    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        is_pinned: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Rename or pin/unpin conversation session."""
        now_iso = datetime.now(timezone.utc).isoformat()
        async with get_db_connection() as db:
            updates = []
            params = []
            if title is not None:
                updates.append("title = ?")
                params.append(title.strip() or "Untitled Research")
            if is_pinned is not None:
                updates.append("is_pinned = ?")
                params.append(1 if is_pinned else 0)

            if not updates:
                return await self.get_session_by_id(session_id)

            updates.append("updated_at = ?")
            params.append(now_iso)
            params.append(session_id)

            query = f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?"
            cursor = await db.execute(query, tuple(params))
            if cursor.rowcount == 0:
                return None
            await db.commit()

        # Update in MongoDB if available
        mongo = get_mongo_db()
        if mongo:
            try:
                m_updates = {"updated_at": now_iso}
                if title is not None:
                    m_updates["title"] = title.strip()
                if is_pinned is not None:
                    m_updates["is_pinned"] = is_pinned
                await mongo.chat_sessions.update_one({"id": session_id}, {"$set": m_updates})
            except Exception as e:
                logger.debug(f"MongoDB update deferred: {e}")

        return await self.get_session_by_id(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session and all associated turns."""
        async with get_db_connection() as db:
            await db.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            cursor = await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            await db.commit()
            success = cursor.rowcount > 0

        mongo = get_mongo_db()
        if mongo:
            try:
                await mongo.chat_messages.delete_many({"session_id": session_id})
                await mongo.chat_sessions.delete_one({"id": session_id})
            except Exception as e:
                logger.debug(f"MongoDB delete deferred: {e}")

        return success

    async def save_message(
        self,
        session_id: str,
        user_id: str,
        sender: str,
        text: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        retrieval_trace: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persist a single conversational message turn with citations and telemetry trace."""
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        citations_json = json.dumps(citations or [])
        trace_json = json.dumps(retrieval_trace or {})

        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO chat_messages (
                    id, session_id, user_id, sender, text, citations,
                    retrieval_trace, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, user_id, sender, text, citations_json, trace_json, now_iso),
            )
            # Update parent session's updated_at
            await db.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (now_iso, session_id),
            )
            await db.commit()

        mongo = get_mongo_db()
        if mongo:
            try:
                await mongo.chat_messages.insert_one({
                    "id": msg_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "sender": sender,
                    "text": text,
                    "citations": citations or [],
                    "retrieval_trace": retrieval_trace or {},
                    "created_at": now_iso,
                })
            except Exception as e:
                logger.debug(f"MongoDB message sync deferred: {e}")

        return {
            "id": msg_id,
            "session_id": session_id,
            "user_id": user_id,
            "sender": sender,
            "text": text,
            "citations": citations or [],
            "retrieval_trace": retrieval_trace or {},
            "created_at": now_iso,
        }

    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve full chronological turns for a session."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT id, session_id, user_id, sender, text, citations, retrieval_trace,
                       feedback_rating, feedback_comment, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            messages = []
            for r in rows:
                try:
                    cites = json.loads(r["citations"])
                except Exception:
                    cites = []
                try:
                    trace = json.loads(r["retrieval_trace"])
                except Exception:
                    trace = {}

                messages.append({
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "user_id": r["user_id"],
                    "sender": r["sender"],
                    "text": r["text"],
                    "citations": cites,
                    "retrieval_trace": trace,
                    "feedback_rating": r["feedback_rating"],
                    "feedback_comment": r["feedback_comment"],
                    "created_at": r["created_at"],
                })
            return messages

    async def record_feedback(
        self,
        message_id: str,
        rating: int,
        comment: Optional[str] = None,
    ) -> bool:
        """Record user feedback on assistant message."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                UPDATE chat_messages
                SET feedback_rating = ?, feedback_comment = ?
                WHERE id = ?
                """,
                (rating, comment, message_id),
            )
            await db.commit()
            return cursor.rowcount > 0


_conv_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    global _conv_service
    if _conv_service is None:
        _conv_service = ConversationService()
    return _conv_service
