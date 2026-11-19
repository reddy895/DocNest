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


def test_research_generators(client, monkeypatch):
    from backend.app.services.ollama_service import OllamaService
    async def mock_generate(*args, **kwargs):
        prompt = kwargs.get("prompt", "")
        if "quiz" in prompt.lower():
            return '[{"id": "q1", "question": "What is AI?", "options": ["ML", "DB", "CSS", "HTML"], "correct_answer": "ML", "explanation": "ML is subfield", "citation": "[Resume.pdf, p. 1]"}]'
        elif "flashcard" in prompt.lower():
            return '[{"id": "fc1", "front": "RAG", "back": "Retrieval-Augmented Generation", "category": "AI", "citation": "[Resume.pdf, p. 1]"}]'
        else:
            return '["What are the key technical skills?", "How was the pipeline designed?"]'
    monkeypatch.setattr(OllamaService, "generate_response", mock_generate)

    # 1. Questions
    res_q = client.post("/api/research/generate-questions", json={"count": 3})
    assert res_q.status_code == 200
    assert len(res_q.json()["questions"]) > 0

    # 2. Quiz
    res_quiz = client.post("/api/research/generate-quiz", json={"question_count": 2})
    assert res_quiz.status_code == 200
    assert len(res_quiz.json()["quiz"]) > 0

    # 3. Flashcards
    res_fc = client.post("/api/research/generate-flashcards", json={"card_count": 2})
    assert res_fc.status_code == 200
    assert len(res_fc.json()["flashcards"]) > 0


def test_research_notes_crud_and_export(client):
    # 1. Create note
    payload = {
        "title": "Quantum RAG Notes",
        "content": "Detailed synthesis regarding vector representations.",
        "tags": ["rag", "ai"],
        "source_citations": [{"filename": "Resume.pdf", "page_number": 1}],
    }
    create_res = client.post("/api/research/notes", json=payload)
    assert create_res.status_code == 201
    note = create_res.json()
    note_id = note["id"]
    assert note["title"] == "Quantum RAG Notes"

    # 2. List notes
    list_res = client.get("/api/research/notes")
    assert list_res.status_code == 200
    assert any(n["id"] == note_id for n in list_res.json())

    # 3. Update note
    patch_res = client.patch(f"/api/research/notes/{note_id}", json={"title": "Updated Quantum RAG"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Quantum RAG"

    # 4. Export markdown
    export_res = client.get(f"/api/research/notes/{note_id}/export")
    assert export_res.status_code == 200
    assert "# Updated Quantum RAG" in export_res.text
    assert "Resume.pdf" in export_res.text

    # 5. Delete note
    del_res = client.delete(f"/api/research/notes/{note_id}")
    assert del_res.status_code == 204





