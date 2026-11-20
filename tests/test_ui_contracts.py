import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_session_contract_for_ui_sidebar(client):
    """
    Ensure /api/chat/sessions returns expected schema for pinned & recent sidebar lists.
    """
    # 1. Create a session
    res = client.post("/api/chat/sessions", json={"title": "UI Contract Test Session"})
    assert res.status_code in [200, 201]
    created = res.json()
    assert "id" in created
    assert created["title"] == "UI Contract Test Session"
    assert created["is_pinned"] is False
    sess_id = created["id"]

    # 2. Toggle pin
    pin_res = client.patch(f"/api/chat/sessions/{sess_id}", json={"is_pinned": True})
    assert pin_res.status_code in [200, 201]
    assert pin_res.json()["is_pinned"] is True

    # 3. List sessions
    list_res = client.get("/api/chat/sessions")
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert any(s["id"] == sess_id and s["is_pinned"] is True for s in sessions)

    # 4. Cleanup
    del_res = client.delete(f"/api/chat/sessions/{sess_id}")
    assert del_res.status_code in [200, 204]


def test_system_status_contract_for_ui_pills(client):
    """
    Ensure /api/health provides structured components for sidebar status indicators.
    """
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "components" in data
    assert "ollama" in data["components"]
    assert "rag" in data["components"]
