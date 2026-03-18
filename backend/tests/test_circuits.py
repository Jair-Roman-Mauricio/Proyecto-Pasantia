"""Tests for /circuits — list, create, delete (cascade), update."""
import pytest

from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit

CIRCUITS_URL = "/api/v1/circuits"


async def test_admin_lists_circuits_by_bar(client, admin_user, admin_token, bar, circuit):
    resp = await client.get(
        f"{CIRCUITS_URL}/bar/{bar.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    denoms = [c["denomination"] for c in resp.json()]
    assert "C-01" in denoms


async def test_admin_creates_circuit(client, admin_user, admin_token, bar, db):
    payload = {
        "denomination": "C-99",
        "name": "Test Circuit",
        "pi_kw": "5.00",
        "fd": "0.8",
        "status": "operative_normal",
        "force": True,
    }
    resp = await client.post(
        f"{CIRCUITS_URL}/bar/{bar.id}",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["denomination"] == "C-99"
    assert db.query(Circuit).filter(Circuit.denomination == "C-99").first() is not None


async def test_opersac_cannot_create_circuit(client, opersac_user, opersac_token, bar):
    payload = {
        "denomination": "C-99",
        "name": "Test Circuit",
        "pi_kw": "5.00",
        "fd": "0.8",
        "status": "operative_normal",
        "force": True,
    }
    resp = await client.post(
        f"{CIRCUITS_URL}/bar/{bar.id}",
        json=payload,
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 403


async def test_circuit_bar_not_found(client, admin_user, admin_token):
    payload = {
        "denomination": "C-99",
        "name": "Test",
        "pi_kw": "5.00",
        "fd": "0.8",
        "status": "operative_normal",
        "force": True,
    }
    resp = await client.post(
        f"{CIRCUITS_URL}/bar/99999",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


async def test_delete_circuit_cascades_sub_circuits(client, admin_user, admin_token, circuit, db):
    # Add a sub-circuit manually
    sub = SubCircuit(
        circuit_id=circuit.id,
        name="Sub 01",
        pi_kw=2,
        fd=1.0,
        md_kw=2,
    )
    db.add(sub)
    db.flush()

    resp = await client.delete(
        f"{CIRCUITS_URL}/{circuit.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    # Sub-circuit should be gone too (cascade)
    assert db.query(SubCircuit).filter(SubCircuit.circuit_id == circuit.id).first() is None


async def test_update_pi_kw_recalculates_md_kw(client, admin_user, admin_token, circuit):
    resp = await client.put(
        f"{CIRCUITS_URL}/{circuit.id}",
        json={"pi_kw": "20.00", "fd": "0.5"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["pi_kw"]) == pytest.approx(20.0)
    assert float(data["md_kw"]) == pytest.approx(10.0)
