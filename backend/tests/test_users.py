"""Tests for /users — list, create, delete, update."""
import uuid

import pytest

from app.models.user import User

USERS_URL = "/api/v1/users"


async def test_admin_can_list_users(client, admin_user, admin_token):
    resp = await client.get(USERS_URL, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "admin_test" in usernames


async def test_opersac_cannot_list_users(client, opersac_user, opersac_token):
    resp = await client.get(USERS_URL, headers={"Authorization": f"Bearer {opersac_token}"})
    assert resp.status_code == 403


async def test_admin_creates_user(client, admin_user, admin_token, db):
    resp = await client.post(
        USERS_URL,
        json={"username": "new_op", "full_name": "New Op", "role": "opersac", "password": "pass123"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "new_op"
    # User should be in DB
    assert db.query(User).filter(User.username == "new_op").first() is not None


async def test_create_duplicate_username(client, admin_user, admin_token):
    payload = {"username": "dup_user", "full_name": "Dup", "role": "opersac", "password": "pass123"}
    await client.post(USERS_URL, json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    resp = await client.post(USERS_URL, json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400


async def test_admin_cannot_delete_self(client, admin_user, admin_token):
    resp = await client.delete(
        f"{USERS_URL}/{admin_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400


async def test_delete_nonexistent_user(client, admin_user, admin_token):
    fake_id = str(uuid.uuid4())
    resp = await client.delete(
        f"{USERS_URL}/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


async def test_update_user_invalid_status(client, admin_user, admin_token, opersac_user):
    resp = await client.put(
        f"{USERS_URL}/{opersac_user.id}",
        json={"status": "flying"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
