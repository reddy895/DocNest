import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from backend.app.core.database import get_db_connection
from backend.app.core.mongo import get_mongo_db

logger = logging.getLogger("docnest.workspaces")


class WorkspaceService:
    """
    Manages workspace lifecycle, multi-tenant document isolation, and ownership.
    """

    async def create_workspace(
        self,
        user_id: str,
        name: str,
        description: str = "",
        color: str = "#F5C542",
        is_default: bool = False,
    ) -> Dict[str, Any]:
        """Create a new research workspace for a user."""
        ws_id = f"ws_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO workspaces (id, user_id, name, description, color, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ws_id, user_id, name.strip(), description.strip(), color, 1 if is_default else 0, now_iso, now_iso),
            )
            await db.commit()

        # Sync to MongoDB if online
        mongo = get_mongo_db()
        if mongo:
            try:
                await mongo.workspaces.insert_one({
                    "id": ws_id,
                    "user_id": user_id,
                    "name": name.strip(),
                    "description": description.strip(),
                    "color": color,
                    "is_default": is_default,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                })
            except Exception as e:
                logger.debug(f"MongoDB workspace sync deferred: {e}")

        return {
            "id": ws_id,
            "user_id": user_id,
            "name": name.strip(),
            "description": description.strip(),
            "color": color,
            "is_default": is_default,
            "created_at": now_iso,
            "updated_at": now_iso,
            "document_count": 0,
        }

    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """List all workspaces belonging to user with document counts."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT w.*, COUNT(d.id) as doc_count
                FROM workspaces w
                LEFT JOIN documents d ON d.workspace_id = w.id
                WHERE w.user_id = ?
                GROUP BY w.id
                ORDER BY w.is_default DESC, w.created_at ASC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()

            # Ensure default workspace exists for user if none found
            if not rows:
                default_ws = await self.create_workspace(
                    user_id=user_id,
                    name="Default Workspace",
                    description="Primary research repository",
                    is_default=True,
                )
                return [default_ws]

            return [
                {
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "name": r["name"],
                    "description": r["description"],
                    "color": r["color"],
                    "is_default": bool(r["is_default"]),
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "document_count": r["doc_count"],
                }
                for r in rows
            ]

    async def get_workspace_by_id(self, workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific workspace ensuring ownership."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT w.*, COUNT(d.id) as doc_count
                FROM workspaces w
                LEFT JOIN documents d ON d.workspace_id = w.id
                WHERE w.id = ? AND w.user_id = ?
                GROUP BY w.id
                """,
                (workspace_id, user_id),
            )
            r = await cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "user_id": r["user_id"],
                "name": r["name"],
                "description": r["description"],
                "color": r["color"],
                "is_default": bool(r["is_default"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "document_count": r["doc_count"],
            }

    async def update_workspace(
        self,
        workspace_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update workspace metadata."""
        now_iso = datetime.now(timezone.utc).isoformat()
        async with get_db_connection() as db:
            updates = []
            params = []
            if name is not None:
                updates.append("name = ?")
                params.append(name.strip())
            if description is not None:
                updates.append("description = ?")
                params.append(description.strip())
            if color is not None:
                updates.append("color = ?")
                params.append(color.strip())

            if not updates:
                return await self.get_workspace_by_id(workspace_id, user_id)

            updates.append("updated_at = ?")
            params.append(now_iso)
            params.extend([workspace_id, user_id])

            query = f"UPDATE workspaces SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            cursor = await db.execute(query, tuple(params))
            if cursor.rowcount == 0:
                return None
            await db.commit()

        return await self.get_workspace_by_id(workspace_id, user_id)

    async def delete_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Delete workspace, reassigning its documents to the default workspace."""
        async with get_db_connection() as db:
            # Check workspace ownership
            cursor = await db.execute("SELECT is_default FROM workspaces WHERE id = ? AND user_id = ?", (workspace_id, user_id))
            ws = await cursor.fetchone()
            if not ws or ws["is_default"]:
                return False  # Cannot delete default workspace or non-existent

            # Find user default workspace
            cursor = await db.execute("SELECT id FROM workspaces WHERE user_id = ? AND is_default = 1", (user_id,))
            default_ws = await cursor.fetchone()
            fallback_id = default_ws["id"] if default_ws else "Default Workspace"

            # Reassign documents
            await db.execute(
                "UPDATE documents SET workspace_id = ? WHERE workspace_id = ? AND user_id = ?",
                (fallback_id, workspace_id, user_id),
            )
            await db.execute("DELETE FROM workspaces WHERE id = ? AND user_id = ?", (workspace_id, user_id))
            await db.commit()

        return True

    async def assign_document_to_workspace(
        self,
        document_id: str,
        workspace_id: str,
        user_id: str,
    ) -> bool:
        """Assign an existing document to a workspace."""
        async with get_db_connection() as db:
            cursor = await db.execute(
                "UPDATE documents SET workspace_id = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (workspace_id, datetime.now(timezone.utc).isoformat(), document_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0


_workspace_service: Optional[WorkspaceService] = None


def get_workspace_service() -> WorkspaceService:
    global _workspace_service
    if _workspace_service is None:
        _workspace_service = WorkspaceService()
    return _workspace_service
