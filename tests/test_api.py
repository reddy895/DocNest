import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DocNest API"
    assert data["status"] == "operational"

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "ollama" in data["components"]

def test_documents_list_endpoint(client):
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "documents" in data

def test_chat_suggestions_endpoint(client):
    response = client.get("/api/chat/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0

def test_upload_invalid_file(client):
    # Upload unsupported file format
    files = {"file": ("test.sh", b"#!/bin/bash\necho hello", "application/x-sh")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code in [400, 422]


def test_summarize_endpoint(client, monkeypatch):
    from backend.app.services.ollama_service import OllamaService
    async def mock_generate(*args, **kwargs):
        return "Executive Brief: Test summary with [Resume.pdf, p. 1]."
    monkeypatch.setattr(OllamaService, "generate_response", mock_generate)

    payload = {"summary_type": "executive"}
    response = client.post("/api/research/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary_type" in data
    assert "content" in data
    assert "sources_used" in data


def test_compare_endpoint(client, monkeypatch):
    from backend.app.services.ollama_service import OllamaService
    async def mock_generate(*args, **kwargs):
        return '{"overview": "Comparison synthesis", "agreements": ["Both support AI"], "contradictions": [], "matrix": "| A | B |\\n|---|---|"}'
    monkeypatch.setattr(OllamaService, "generate_response", mock_generate)

    payload = {"doc_ids": ["doc_4617cec4d59c", "doc_b8359c5aacc5"]}
    response = client.post("/api/research/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    assert "agreements" in data
    assert "contradictions" in data



