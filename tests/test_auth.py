import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import hash_password, verify_password, create_access_token, decode_access_token

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("WrongPassword!", hashed)

def test_jwt_token_roundtrip():
    data = {"sub": "user_123", "role": "admin"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_123"
    assert decoded["role"] == "admin"

def test_user_registration_and_login_flow(client):
    email = f"test_{pytest.__version__}@docnest.ai"
    reg_payload = {
        "email": email,
        "username": "TestEngineer",
        "password": "Password789!",
        "workspace_name": "QA Workspace"
    }
    
    # 1. Register
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code in [201, 400]
    
    # 2. Login
    login_resp = client.post("/api/auth/login", json={"email": email, "password": "Password789!"})
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["user"]["email"] == email
    
    # 3. Authenticated /me
    token = token_data["access_token"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == email
    assert me_data["workspace_name"] == "QA Workspace"

def test_login_invalid_password(client):
    resp = client.post("/api/auth/login", json={"email": "nonexistent@docnest.ai", "password": "wrong"})
    assert resp.status_code == 401
