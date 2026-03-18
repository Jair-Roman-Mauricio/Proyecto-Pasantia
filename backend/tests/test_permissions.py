"""Tests for /permissions — own permissions, admin reads/writes."""
import uuid

import pytest

from app.models.permission import Permission

PERMISSIONS_URL = "/api/v1/permissions"


async def test_opersac_gets_own_permissions(client, opersac_user, opersac_token):
    resp = await client.get(
        f"{PERMISSIONS_URL}/me",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200
    keys = [p["feature_key"] for p in resp.json()]
    assert "view_stations" in keys


async def test_unauthenticated_cannot_get_permissions(client):
    resp = await client.get(f"{PERMISSIONS_URL}/me")
    assert resp.status_code == 401


async def test_admin_gets_user_permissions(client, admin_user, admin_token, opersac_user):
    resp = await client.get(
        f"{PERMISSIONS_URL}/users/{opersac_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_opersac_cannot_get_other_user_permissions(client, opersac_user, opersac_token, admin_user):
    resp = await client.get(
        f"{PERMISSIONS_URL}/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 403


async def test_admin_updates_permissions(client, admin_user, admin_token, opersac_user, db):
    resp = await client.put(
        f"{PERMISSIONS_URL}/users/{opersac_user.id}",
        json={
            "permissions": [
                {"feature_key": "view_stations", "is_allowed": False},
                {"feature_key": "send_requests", "is_allowed": True},
            ]
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    perm = (
        db.query(Permission)
        .filter(
            Permission.user_id == opersac_user.id,
            Permission.feature_key == "view_stations",
        )
        .first()
    )
    assert perm is not None
    assert perm.is_allowed is False
