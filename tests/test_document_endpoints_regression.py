"""Regression tests for document preview, raw text inspection, workspaces, and models API."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.core.database import db_manager, get_db_connection


@pytest_asyncio.fixture(autouse=True)
async def ensure_db_ready():
    await db_manager.init_db()
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (id, email, username, password_hash)
            VALUES ('user_default_local', 'local@docnest.ai', 'Local Operator', 'hashed_local_pass')
            """
        )
        await db.commit()


@pytest.mark.asyncio
async def test_document_preview_and_raw_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        prev = await ac.get("/api/documents/nonexistent_doc_999/preview")
        assert prev.status_code == 404

        raw = await ac.get("/api/documents/nonexistent_doc_999/raw")
        assert raw.status_code == 200
        body = raw.json()
        assert body["doc_id"] == "nonexistent_doc_999"
        assert body["total_chunks"] == 0


@pytest.mark.asyncio
async def test_workspaces_and_models_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ws_list = await ac.get("/api/workspaces")
        assert ws_list.status_code == 200
        assert isinstance(ws_list.json(), list)

        models_res = await ac.get("/api/models")
        assert models_res.status_code == 200
        models_data = models_res.json()
        assert isinstance(models_data, list) and len(models_data) > 0
        assert "id" in models_data[0] and "provider" in models_data[0]
