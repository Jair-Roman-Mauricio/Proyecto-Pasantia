"""Tests for GET /auth/me — token validation and user lookup."""
import time
import uuid

import pytest
from jose import jwt

from app.models.user import User

JWT_SECRET = "test-secret-for-pytest-hs256"
AUTH_ME = "/api/v1/auth/me"


async def test_auth_me_valid_token(client, admin_user, admin_token):
    resp = await client.get(AUTH_ME, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin_test"
    assert data["role"] == "admin"


async def test_auth_me_no_token(client):
    resp = await client.get(AUTH_ME)
    assert resp.status_code == 401


async def test_auth_me_malformed_token(client):
    resp = await client.get(AUTH_ME, headers={"Authorization": "Bearer not.a.token"})
    assert resp.status_code == 401


async def test_auth_me_expired_token(client, admin_user):
    expired = jwt.encode(
        {"sub": str(admin_user.id), "exp": time.time() - 1},
        JWT_SECRET,
        algorithm="HS256",
    )
    resp = await client.get(AUTH_ME, headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


async def test_auth_me_inactive_user(client, db):
    inactive = User(
        id=uuid.uuid4(),
        username="inactive_user",
        full_name="Inactive",
        role="opersac",
        status="inactive",
    )
    db.add(inactive)
    db.flush()
    token = jwt.encode(
        {"sub": str(inactive.id), "exp": time.time() + 3600},
        JWT_SECRET,
        algorithm="HS256",
    )
    resp = await client.get(AUTH_ME, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
