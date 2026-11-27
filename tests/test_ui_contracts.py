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


def test_chatgpt_frontend_components_and_palette():
    """
    Verify modular ChatGPT-style frontend components, neutral dark palette,
    welcome copy, and composer disclaimer exist without yellow-heavy branding.
    """
    from pathlib import Path

    root = Path("frontend/src")
    required_components = [
        root / "components/sidebar/Sidebar.jsx",
        root / "components/sidebar/ConversationList.jsx",
        root / "components/chat/ChatHeader.jsx",
        root / "components/chat/ChatContainer.jsx",
        root / "components/chat/UserMessage.jsx",
        root / "components/chat/AssistantMessage.jsx",
        root / "components/chat/MarkdownRenderer.jsx",
        root / "components/chat/CitationChip.jsx",
        root / "components/chat/CodeBlock.jsx",
        root / "components/chat/ThinkingIndicator.jsx",
        root / "components/chat/RetrievalStatus.jsx",
        root / "components/chat/ChatComposer.jsx",
        root / "components/chat/ModelSelector.jsx",
        root / "components/chat/WelcomeScreen.jsx",
    ]
    for path in required_components:
        assert path.exists(), f"Missing component: {path}"

    welcome = (root / "components/chat/WelcomeScreen.jsx").read_text()
    assert "What can I help you understand?" in welcome
    assert "Explore your documents, uncover insights, and research with AI." in welcome

    composer = (root / "components/chat/ChatComposer.jsx").read_text()
    assert "DocNest can make mistakes. Verify important information with the original sources." in composer
    assert "#303030" in composer

    sidebar = (root / "components/sidebar/Sidebar.jsx").read_text()
    assert "#171717" in sidebar
    assert "#F5C542" not in sidebar

    retrieval_status = (root / "components/chat/RetrievalStatus.jsx").read_text()
    assert "Thinking..." in retrieval_status
    assert "Searching your documents..." in retrieval_status
    assert "Analyzing retrieved information..." in retrieval_status
    assert "Preparing your answer..." in retrieval_status

    logo_png = Path("frontend/public/docnest-logo.png")
    assert logo_png.exists(), "Missing transparent docnest-logo.png"
    assert "/docnest-logo.png" in sidebar
    assert "/docnest-logo.png" in (root / "components/layout/AppShell.jsx").read_text()
    assert "/docnest-logo.png" in (root / "components/chat/AssistantMessage.jsx").read_text()
    assert "/docnest-logo.png" in Path("frontend/index.html").read_text()

