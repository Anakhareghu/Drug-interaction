import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_login_success():
    """Test login with valid default admin credentials."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": settings.DEFAULT_AUTH_USERNAME, "password": settings.DEFAULT_AUTH_PASSWORD}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == settings.DEFAULT_AUTH_USERNAME
    assert data["user"]["role"] == settings.DEFAULT_AUTH_ROLE

def test_login_invalid_password():
    """Test login fails with incorrect password."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": settings.DEFAULT_AUTH_USERNAME, "password": "wrongpassword999"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

def test_login_unknown_user():
    """Test login fails with non-existent user."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": "nonexistent_pharmacist", "password": "anypassword"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

def test_get_current_user_valid_token():
    """Test GET /api/auth/me with valid Bearer token."""
    login_resp = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": settings.DEFAULT_AUTH_USERNAME, "password": settings.DEFAULT_AUTH_PASSWORD}
    )
    token = login_resp.json()["access_token"]
    
    me_resp = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == settings.DEFAULT_AUTH_USERNAME
    assert me_data["role"] == settings.DEFAULT_AUTH_ROLE

def test_get_current_user_missing_token():
    """Test GET /api/auth/me fails when Authorization header is missing."""
    response = client.get(f"{settings.API_V1_STR}/auth/me")
    assert response.status_code == 401
    assert "Authentication credentials were not provided" in response.json()["detail"]

def test_get_current_user_invalid_token():
    """Test GET /api/auth/me fails with malformed or tampered token."""
    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": "Bearer totally.invalid.jwt.token"}
    )
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]

def test_logout_endpoint():
    """Test POST /api/auth/logout with valid token."""
    login_resp = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"username": settings.DEFAULT_AUTH_USERNAME, "password": settings.DEFAULT_AUTH_PASSWORD}
    )
    token = login_resp.json()["access_token"]
    
    logout_resp = client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200
    assert "successfully ended" in logout_resp.json()["message"]

def test_logout_without_token():
    """Test POST /api/auth/logout fails without Authorization token."""
    response = client.post(f"{settings.API_V1_STR}/auth/logout")
    assert response.status_code == 401
