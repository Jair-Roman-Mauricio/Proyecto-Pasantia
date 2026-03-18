"""
Tests para /bars — listar, obtener, resumen de potencia, actualizar capacidad.
Cubre la Tarea 2 (Pruebas funcionales del sistema) de la Etapa 04.
"""
import pytest

from app.models.bar import Bar
from app.models.circuit import Circuit

BARS_URL = "/api/v1/bars"


# ---------------------------------------------------------------------------
# Listar barras de una estación
# ---------------------------------------------------------------------------

async def test_admin_lists_bars_by_station(client, admin_user, admin_token, bar, station):
    resp = await client.get(
        f"{BARS_URL}/station/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    types = [b["bar_type"] for b in resp.json()]
    assert "normal" in types


async def test_opersac_lists_bars_with_permission(client, opersac_user, opersac_token, bar, station):
    resp = await client.get(
        f"{BARS_URL}/station/{station.id}",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200


async def test_opersac_without_permission_denied_bars(client, db, station):
    import uuid
    from tests.conftest import make_token
    from app.models.user import User

    user = User(
        id=uuid.uuid4(), username="noperm_bars", full_name="No Perm",
        role="opersac", status="active",
    )
    db.add(user)
    db.flush()

    token = make_token(str(user.id))
    resp = await client.get(
        f"{BARS_URL}/station/{station.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_get_bar_by_id(client, admin_user, admin_token, bar):
    resp = await client.get(
        f"{BARS_URL}/{bar.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["bar_type"] == "normal"
    assert resp.json()["id"] == bar.id


async def test_get_nonexistent_bar(client, admin_user, admin_token):
    resp = await client.get(
        f"{BARS_URL}/99999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Resumen de potencia de una barra
# ---------------------------------------------------------------------------

async def test_bar_power_summary_empty(client, admin_user, admin_token, bar):
    """Barra sin circuitos → MD total = 0, disponible = capacidad."""
    resp = await client.get(
        f"{BARS_URL}/{bar.id}/power-summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_max_demand_kw"] == pytest.approx(0.0)
    assert data["max_board_capacity_kw"] == pytest.approx(200.0)
    assert data["available_power_kw"] == pytest.approx(200.0)


async def test_bar_power_summary_with_circuit(client, admin_user, admin_token, bar, circuit):
    """Barra con un circuito (md_kw=8) → MD total = 8."""
    resp = await client.get(
        f"{BARS_URL}/{bar.id}/power-summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_max_demand_kw"] == pytest.approx(8.0)
    assert data["available_power_kw"] == pytest.approx(192.0)


async def test_bar_power_summary_nonexistent(client, admin_user, admin_token):
    resp = await client.get(
        f"{BARS_URL}/99999/power-summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Actualizar capacidad de una barra
# ---------------------------------------------------------------------------

async def test_admin_updates_bar_capacity(client, admin_user, admin_token, bar, db):
    resp = await client.put(
        f"{BARS_URL}/{bar.id}/capacity",
        json={"capacity_kw": "350.00", "capacity_a": "500.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["capacity_kw"]) == pytest.approx(350.0)
    assert float(data["capacity_a"]) == pytest.approx(500.0)

    # Verificar que el cambio persiste en la BD
    db.expire(bar)
    db.refresh(bar)
    assert float(bar.capacity_kw) == pytest.approx(350.0)


async def test_opersac_cannot_update_bar_capacity(client, opersac_user, opersac_token, bar):
    resp = await client.put(
        f"{BARS_URL}/{bar.id}/capacity",
        json={"capacity_kw": "350.00", "capacity_a": "500.00"},
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 403


async def test_update_capacity_nonexistent_bar(client, admin_user, admin_token):
    resp = await client.put(
        f"{BARS_URL}/99999/capacity",
        json={"capacity_kw": "200.00", "capacity_a": "300.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404
