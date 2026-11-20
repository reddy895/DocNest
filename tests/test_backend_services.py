import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.database import db_manager, get_db_connection
from backend.app.services.auth_service import get_auth_service
from backend.app.services.workspace_service import get_workspace_service
from backend.app.services.conversation_service import get_conversation_service
from backend.app.services.model_config_service import get_model_config_service
from backend.app.services.settings_service import get_settings_service


@pytest_asyncio.fixture(autouse=True)
async def ensure_db_ready():
    """Ensure SQLite schema and default local user exist."""
    await db_manager.init_db()
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (id, email, username, password_hash, workspace_name, created_at)
            VALUES ('user_default_local', 'local@docnest.ai', 'Local Operator', '', 'Default Workspace', datetime('now'))
            """
        )
        await db.commit()


@pytest.mark.asyncio
async def test_auth_service_password_and_jwt():
    """Verify password hashing security and JWT encode/decode lifecycle."""
    auth = get_auth_service()
    raw_pwd = "SecureResearchPass99!"

    # 1. Hashing
    hashed = auth.hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert auth.verify_password(raw_pwd, hashed)
    assert not auth.verify_password("WrongPassword123", hashed)

    # 2. Token creation and validation
    access_tok = auth.create_access_token({"sub": "user_default_local", "email": "local@docnest.ai"})
    payload = auth.decode_token(access_tok)
    assert payload is not None
    assert payload["sub"] == "user_default_local"
    assert payload["type"] == "access"

    # 3. Refresh token creation
    refresh_tok = auth.create_refresh_token("user_default_local")
    ref_payload = auth.decode_token(refresh_tok)
    assert ref_payload is not None
    assert ref_payload["sub"] == "user_default_local"
    assert ref_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_auth_api_endpoints():
    """Test /api/auth/register, /api/auth/login, /api/auth/refresh, and /api/auth/me."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        unique_email = "researcher_42@docnest.ai"

        # Register
        reg_res = await ac.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "username": "Dr. Researcher",
                "password": "Password789!",
                "workspace_name": "Biomedical Lab",
            },
        )
        assert reg_res.status_code in [201, 400]  # 400 if already created in earlier run

        # Login
        login_res = await ac.post(
            "/api/auth/login",
            json={"email": unique_email, "password": "Password789!"},
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data

        # Refresh
        ref_res = await ac.post(
            "/api/auth/refresh",
            json={"refresh_token": token_data["refresh_token"]},
        )
        assert ref_res.status_code == 200
        assert "access_token" in ref_res.json()

        # Me
        me_res = await ac.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == unique_email


@pytest.mark.asyncio
async def test_workspace_service_lifecycle():
    """Verify workspace CRUD and multi-tenant scoping."""
    ws_svc = get_workspace_service()
    user_id = "user_default_local"

    # Create
    ws = await ws_svc.create_workspace(
        user_id=user_id,
        name="Clinical Trials 2026",
        description="Phase III studies",
        color="#F5C542",
    )
    assert ws["name"] == "Clinical Trials 2026"
    assert ws["is_default"] is False

    # Get by ID
    fetched = await ws_svc.get_workspace_by_id(ws["id"], user_id)
    assert fetched is not None
    assert fetched["id"] == ws["id"]

    # Update
    updated = await ws_svc.update_workspace(ws["id"], user_id, name="Clinical Trials 2026 - Extended")
    assert updated["name"] == "Clinical Trials 2026 - Extended"

    # Delete
    deleted = await ws_svc.delete_workspace(ws["id"], user_id)
    assert deleted is True


@pytest.mark.asyncio
async def test_conversation_service_and_api():
    """Verify conversation sessions, message turns, full-text search, and pagination."""
    conv_svc = get_conversation_service()
    user_id = "user_default_local"

    # Create session
    sess = await conv_svc.create_session(user_id=user_id, title="NLP Benchmark Review")
    assert sess["id"].startswith("sess_")

    # Add message turn
    msg = await conv_svc.save_message(
        session_id=sess["id"],
        user_id=user_id,
        sender="user",
        text="Compare RRF fusion against dense-only retrieval.",
    )
    assert msg["sender"] == "user"

    # Search conversations
    items, total = await conv_svc.get_user_sessions(user_id=user_id, search_query="Benchmark")
    assert total >= 1
    assert any(s["id"] == sess["id"] for s in items)

    # API contract
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/conversations?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data

    # Cleanup
    await conv_svc.delete_session(sess["id"])


@pytest.mark.asyncio
async def test_model_config_and_settings_services():
    """Verify model discovery list and user pipeline settings presets."""
    model_svc = get_model_config_service()
    models = await model_svc.list_available_models(force_refresh=False)
    assert len(models) >= 5
    assert any(m["id"] in ["llama3.2", "llama3.2:latest"] for m in models)

    settings_svc = get_settings_service()
    user_id = "user_default_local"
    s = await settings_svc.get_user_settings(user_id)
    assert s.chunk_size == 512

    # Switch preset to deep
    deep_s = await settings_svc.apply_preset(user_id, "deep")
    assert deep_s.top_k == 8
    assert deep_s.preset_name == "deep"

    # Switch back to balanced
    bal_s = await settings_svc.apply_preset(user_id, "balanced")
    assert bal_s.top_k == 5
