"""
Tests para /sub-circuits — listar, crear, eliminar, cambiar estado.
Cubre la Tarea 2 (Pruebas funcionales del sistema) de la Etapa 04.
"""
import pytest

from app.models.sub_circuit import SubCircuit

SUB_URL = "/api/v1/sub-circuits"


# ---------------------------------------------------------------------------
# Listar sub-circuitos
# ---------------------------------------------------------------------------

async def test_admin_lists_sub_circuits(client, admin_user, admin_token, circuit, db):
    sub = SubCircuit(
        circuit_id=circuit.id, name="Sub-01", pi_kw=3, fd=1.0, md_kw=3,
    )
    db.add(sub)
    db.flush()

    resp = await client.get(
        f"{SUB_URL}/circuit/{circuit.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Sub-01"


async def test_opersac_lists_sub_circuits_with_permission(client, opersac_user, opersac_token, circuit):
    resp = await client.get(
        f"{SUB_URL}/circuit/{circuit.id}",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200


async def test_unauthenticated_cannot_list_sub_circuits(client, circuit):
    resp = await client.get(f"{SUB_URL}/circuit/{circuit.id}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Crear sub-circuito
# ---------------------------------------------------------------------------

async def test_admin_creates_sub_circuit(client, admin_user, admin_token, circuit, db):
    resp = await client.post(
        f"{SUB_URL}/circuit/{circuit.id}",
        json={
            "name": "Sub Nuevo",
            "pi_kw": "5.00",
            "fd": "0.8",
            "status": "operative_normal",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Sub Nuevo"
    assert float(data["md_kw"]) == pytest.approx(4.0)  # 5 × 0.8

    assert db.query(SubCircuit).filter(SubCircuit.circuit_id == circuit.id).count() == 1


async def test_opersac_cannot_create_sub_circuit(client, opersac_user, opersac_token, circuit):
    resp = await client.post(
        f"{SUB_URL}/circuit/{circuit.id}",
        json={"name": "Sub Nuevo", "pi_kw": "5.00", "fd": "0.8", "status": "operative_normal"},
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 403


async def test_create_sub_circuit_nonexistent_circuit(client, admin_user, admin_token):
    resp = await client.post(
        f"{SUB_URL}/circuit/99999",
        json={"name": "Sub Nuevo", "pi_kw": "5.00", "fd": "0.8", "status": "operative_normal"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


async def test_create_sub_circuit_md_calculated_automatically(client, admin_user, admin_token, circuit):
    """Si no se envía md_kw, debe calcularse como pi_kw × fd."""
    resp = await client.post(
        f"{SUB_URL}/circuit/{circuit.id}",
        json={"name": "Auto MD", "pi_kw": "10.00", "fd": "0.75", "status": "operative_normal"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert float(resp.json()["md_kw"]) == pytest.approx(7.5)


# ---------------------------------------------------------------------------
# Eliminar sub-circuito
# ---------------------------------------------------------------------------

async def test_admin_deletes_sub_circuit(client, admin_user, admin_token, circuit, db):
    sub = SubCircuit(circuit_id=circuit.id, name="Sub a borrar", pi_kw=2, fd=1.0, md_kw=2)
    db.add(sub)
    db.flush()
    sub_id = sub.id

    resp = await client.delete(
        f"{SUB_URL}/{sub_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert db.query(SubCircuit).filter(SubCircuit.id == sub_id).first() is None


async def test_delete_nonexistent_sub_circuit(client, admin_user, admin_token):
    resp = await client.delete(
        f"{SUB_URL}/99999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cambiar estado del sub-circuito
# ---------------------------------------------------------------------------

async def test_admin_changes_sub_circuit_status_to_reserve(client, admin_user, admin_token, circuit, db):
    sub = SubCircuit(
        circuit_id=circuit.id, name="Sub Estado", pi_kw=3, fd=1.0, md_kw=3,
        status="operative_normal",
    )
    db.add(sub)
    db.flush()

    resp = await client.put(
        f"{SUB_URL}/{sub.id}/status",
        json={"status": "reserve_r", "reserve_expires_at": "2026-12-31"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "reserve_r"
    assert data["reserve_since"] is not None


async def test_status_back_to_operative_clears_reserve_dates(client, admin_user, admin_token, circuit, db):
    sub = SubCircuit(
        circuit_id=circuit.id, name="Sub Reserva", pi_kw=3, fd=1.0, md_kw=3,
        status="reserve_r",
    )
    db.add(sub)
    db.flush()

    resp = await client.put(
        f"{SUB_URL}/{sub.id}/status",
        json={"status": "operative_normal"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operative_normal"
    assert data["reserve_since"] is None
    assert data["reserve_expires_at"] is None
