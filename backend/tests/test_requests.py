"""Tests for /requests — create, approve, reject."""
import pytest

from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.request import Request

REQUESTS_URL = "/api/v1/requests"


async def test_opersac_creates_request(client, opersac_user, opersac_token, station, bar, db):
    resp = await client.post(
        REQUESTS_URL,
        json={
            "station_id": station.id,
            "bar_type": "normal",
            "requested_load_kw": "10.00",
            "fd": "1.0",
            "justification": "Test request",
        },
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert db.query(Request).filter(Request.id == data["id"]).first() is not None


async def test_opersac_without_permission_cannot_create_request(client, db, station):
    import uuid
    from tests.conftest import make_token
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        username="noperm2",
        full_name="No Perm",
        role="opersac",
        status="active",
    )
    db.add(user)
    db.flush()

    token = make_token(str(user.id))
    resp = await client.post(
        REQUESTS_URL,
        json={"station_id": station.id, "bar_type": "normal", "requested_load_kw": "10.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_admin_approves_creates_circuit(client, admin_user, admin_token, opersac_user, station, bar, db):
    # Create a pending request first
    req = Request(
        opersac_user_id=opersac_user.id,
        station_id=station.id,
        bar_type="normal",
        requested_load_kw=10,
        fd=1.0,
        status="pending",
    )
    db.add(req)
    db.flush()

    resp = await client.put(
        f"{REQUESTS_URL}/{req.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    # A new circuit should have been created
    assert db.query(Circuit).filter(Circuit.bar_id == bar.id).count() >= 1


async def test_admin_approves_creates_sub_circuit(client, admin_user, admin_token, opersac_user, circuit, station, bar, db):
    req = Request(
        opersac_user_id=opersac_user.id,
        station_id=station.id,
        bar_type="normal",
        circuit_id=circuit.id,
        requested_load_kw=5,
        fd=1.0,
        sub_circuit_name="New Sub",
        status="pending",
    )
    db.add(req)
    db.flush()

    resp = await client.put(
        f"{REQUESTS_URL}/{req.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert db.query(SubCircuit).filter(SubCircuit.circuit_id == circuit.id).count() >= 1


async def test_admin_rejects_request(client, admin_user, admin_token, opersac_user, station, db):
    req = Request(
        opersac_user_id=opersac_user.id,
        station_id=station.id,
        bar_type="normal",
        requested_load_kw=10,
        fd=1.0,
        status="pending",
    )
    db.add(req)
    db.flush()

    resp = await client.put(
        f"{REQUESTS_URL}/{req.id}/reject",
        json={"rejection_reason": "No hay capacidad disponible"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "No hay capacidad disponible"


async def test_approve_already_approved_request(client, admin_user, admin_token, opersac_user, station, db):
    req = Request(
        opersac_user_id=opersac_user.id,
        station_id=station.id,
        bar_type="normal",
        requested_load_kw=10,
        fd=1.0,
        status="approved",
    )
    db.add(req)
    db.flush()

    resp = await client.put(
        f"{REQUESTS_URL}/{req.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
