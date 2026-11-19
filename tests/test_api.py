import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

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

