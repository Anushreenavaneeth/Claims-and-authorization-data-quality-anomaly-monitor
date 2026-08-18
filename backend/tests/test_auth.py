"""
Authentication & Authorization tests.
Run: pytest tests/ -v
"""
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.config import settings


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success_admin(client, admin_user):
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1234!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "admin"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_login_success_worker(client, worker_user):
    resp = client.post("/auth/login", json={"email": "worker@example.com", "password": "Worker1234!"})
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "worker"


def test_login_wrong_password(client, admin_user):
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


def test_login_missing_email(client):
    resp = client.post("/auth/login", json={"password": "Admin1234!"})
    assert resp.status_code == 422


def test_login_missing_password(client):
    resp = client.post("/auth/login", json={"email": "admin@example.com"})
    assert resp.status_code == 422


def test_login_invalid_email_format(client):
    resp = client.post("/auth/login", json={"email": "not-an-email", "password": "Admin1234!"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

def _auth_header(client, email, password):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_me_valid_token(client, admin_user):
    headers = _auth_header(client, "admin@example.com", "Admin1234!")
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@example.com"


def test_get_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)  # HTTPBearer raises 403; some versions 401


def test_get_me_invalid_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer totally.invalid.token"})
    assert resp.status_code == 401


def test_get_me_expired_token(client, admin_user):
    expired_payload = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role,
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role-based authorization
# ---------------------------------------------------------------------------

def test_admin_can_access_admin_endpoint(client, admin_user):
    headers = _auth_header(client, "admin@example.com", "Admin1234!")
    resp = client.get("/admin/dashboard", headers=headers)
    assert resp.status_code == 200


def test_worker_cannot_access_admin_endpoint(client, worker_user):
    headers = _auth_header(client, "worker@example.com", "Worker1234!")
    resp = client.get("/admin/dashboard", headers=headers)
    assert resp.status_code == 403


def test_worker_can_access_worker_endpoint(client, worker_user):
    headers = _auth_header(client, "worker@example.com", "Worker1234!")
    resp = client.get("/worker/dashboard", headers=headers)
    assert resp.status_code == 200


def test_admin_cannot_access_worker_endpoint(client, admin_user):
    headers = _auth_header(client, "admin@example.com", "Admin1234!")
    resp = client.get("/worker/dashboard", headers=headers)
    assert resp.status_code == 403


def test_unauthenticated_cannot_access_admin(client):
    resp = client.get("/admin/dashboard")
    assert resp.status_code in (401, 403)


def test_unauthenticated_cannot_access_worker(client):
    resp = client.get("/worker/dashboard")
    assert resp.status_code in (401, 403)
