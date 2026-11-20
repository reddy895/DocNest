import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.mongo import mongo_manager, is_mongo_online
from backend.app.core.security import validate_file_size_and_extension
from backend.app.core.config import settings


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_correlation_id_middleware(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-MS" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_custom_correlation_id_propagated(client):
    custom_id = "req_custom_trace_12345"
    response = client.get("/", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_centralized_not_found_handler(client):
    response = client.get("/api/non_existent_endpoint_1234")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] is True
    assert data["status_code"] == 404
    assert "path" in data


def test_mongo_offline_fallback():
    # In test environment, MongoDB is not running by default, must fall back cleanly
    assert is_mongo_online() is False
    assert mongo_manager.db is None


def test_validate_file_size_and_extension():
    # Valid files
    ok, err = validate_file_size_and_extension("report.pdf", 1024)
    assert ok is True
    assert err is None

    ok, err = validate_file_size_and_extension("paper.docx", 2048)
    assert ok is True

    ok, err = validate_file_size_and_extension("notes.txt", 500)
    assert ok is True

    ok, err = validate_file_size_and_extension("dataset.csv", 4000)
    assert ok is True

    # Invalid extension
    ok, err = validate_file_size_and_extension("script.exe", 1024)
    assert ok is False
    assert "Unsupported file extension" in err

    # Oversized file
    huge_bytes = (settings.MAX_FILE_SIZE_MB + 1) * 1024 * 1024
    ok, err = validate_file_size_and_extension("giant.pdf", huge_bytes)
    assert ok is False
    assert "exceeds maximum permitted limit" in err

    # Empty file
    ok, err = validate_file_size_and_extension("empty.pdf", 0)
    assert ok is False
    assert "empty" in err
