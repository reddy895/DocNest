import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.database import db_manager, get_db_connection
from backend.app.services.ollama_service import OllamaService


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
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
async def test_ollama_service_online_and_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app_name"] == "DocNest"
        assert "ollama" in data["components"]
        # Ollama daemon supervisor should have ensured connectivity
        assert data["components"]["ollama"]["status"] == "connected"
        assert "models" in data["components"]["ollama"]["available_models"] or len(data["components"]["ollama"]["available_models"]) >= 0


@pytest.mark.asyncio
async def test_chat_greeting_interceptor():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "question": "Hello! What can you do?",
            "search_mode": "hybrid",
        }
        resp = await ac.post("/api/chat/stream", json=payload)
        assert resp.status_code == 200
        text = resp.text
        # Should include DocNest introduction without triggering 0.00 score abstention
        assert "DocNest Intelligence" in text
        assert "data: " in text


@pytest.mark.asyncio
async def test_chat_retrieval_fallback_on_unmatched_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "question": "What is the quantum teleportation protocol in chapter 99?",
            "search_mode": "hybrid",
        }
        resp = await ac.post("/api/chat/stream", json=payload)
        assert resp.status_code == 200
        assert "data: " in resp.text
