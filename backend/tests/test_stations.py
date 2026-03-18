"""Tests for /stations — list, get, update."""

STATIONS_URL = "/api/v1/stations"


async def test_admin_lists_stations(client, admin_user, admin_token, station):
    resp = await client.get(STATIONS_URL, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    codes = [s["code"] for s in resp.json()]
    assert "E01" in codes


async def test_opersac_with_permission_lists_stations(client, opersac_user, opersac_token, station):
    resp = await client.get(STATIONS_URL, headers={"Authorization": f"Bearer {opersac_token}"})
    assert resp.status_code == 200


async def test_opersac_without_permission_denied(client, db, station):
    import uuid
    from tests.conftest import make_token
    from app.models.user import User
    from app.models.permission import Permission

    user = User(
        id=uuid.uuid4(),
        username="noperm",
        full_name="No Perm",
        role="opersac",
        status="active",
    )
    db.add(user)
    db.flush()
    # Grant only view_reports — NOT view_stations
    db.add(Permission(user_id=user.id, feature_key="view_reports", is_allowed=True))
    db.flush()

    token = make_token(str(user.id))
    resp = await client.get(STATIONS_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_get_nonexistent_station(client, admin_user, admin_token):
    resp = await client.get(f"{STATIONS_URL}/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


async def test_admin_updates_station_capacity(client, admin_user, admin_token, station):
    resp = await client.put(
        f"{STATIONS_URL}/{station.id}",
        json={"transformer_capacity_kw": "600.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert float(resp.json()["transformer_capacity_kw"]) == pytest.approx(600.0)


import pytest
