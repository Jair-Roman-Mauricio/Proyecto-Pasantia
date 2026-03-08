"""
Tests de Aceptación — Flujo completo rol Admin
================================================
Endpoints: /api/v1/auth, /api/v1/stations, /api/v1/circuits, /api/v1/audit

Casos de prueba:
  TC-A01  Admin gestiona un circuito de extremo a extremo:
          login → crear circuito → verificar energía aumentó →
          cambiar estado a reserve_r → verificar audit log →
          eliminar circuito → verificar energía disminuyó

Patrón: Arrange → Act (pasos secuenciales) → Assert por etapa
"""

import pytest
from decimal import Decimal

from app.models.station import Station
from app.models.bar import Bar


# ---------------------------------------------------------------------------
# Fixture: estación + barra con capacidad suficiente
# ---------------------------------------------------------------------------

@pytest.fixture
def setup_station_and_bar(db_session):
    """Estación de 200 kW con barra principal lista para recibir circuitos."""
    station = Station(
        code="ADM01", name="Estacion Admin Flow", order_index=50,
        transformer_capacity_kw=Decimal("200"), max_demand_kw=Decimal("0"),
        available_power_kw=Decimal("200"), status="green",
    )
    db_session.add(station)
    db_session.commit()

    bar = Bar(
        station_id=station.id, name="Barra Principal ADM", bar_type="normal",
        status="operative", capacity_kw=Decimal("200"), capacity_a=Decimal("400"),
    )
    db_session.add(bar)
    db_session.commit()
    db_session.refresh(station)
    db_session.refresh(bar)
    return station, bar


# ---------------------------------------------------------------------------
# TC-A01: Flujo completo admin — circuito de extremo a extremo
# ---------------------------------------------------------------------------

class TestAdminCircuitEndToEnd:
    """
    TC-A01: Admin gestiona un circuito de extremo a extremo.

    Pasos:
      1. GET /stations/{id}         → estado inicial (max_demand_kw = 0)
      2. POST /circuits/bar/{id}    → crear circuito PI=20, FD=0.9 (MD=18)
      3. GET /stations/{id}         → max_demand_kw aumentó a 18
      4. PUT /circuits/{id}/status  → cambiar a reserve_r
      5. GET /audit                 → registro CHANGE_CIRCUIT_STATUS existe
      6. DELETE /circuits/{id}      → eliminar circuito
      7. GET /stations/{id}         → max_demand_kw volvió a 0
    """

    def test_admin_manages_circuit_end_to_end(
        self, client, auth_admin, db_session, admin_user, setup_station_and_bar
    ):
        station, bar = setup_station_and_bar

        # ── Paso 1: Estado inicial de la estación ──────────────────────────
        r = client.get(f"/api/v1/stations/{station.id}", headers=auth_admin)
        assert r.status_code == 200
        initial_demand = r.json()["max_demand_kw"]
        assert float(initial_demand) == 0.0, (
            f"La demanda inicial debe ser 0, obtenida: {initial_demand}"
        )

        # ── Paso 2: Crear circuito PI=20, FD=0.9 → MD=18 ──────────────────
        r = client.post(
            f"/api/v1/circuits/bar/{bar.id}",
            json={
                "denomination": "C-A01",
                "name": "Circuito Admin Flow",
                "pi_kw": 20.0,
                "fd": 0.9,
                "status": "operative_normal",
            },
            headers=auth_admin,
        )
        assert r.status_code == 201, f"Crear circuito falló: {r.text}"
        circuit_data = r.json()
        circuit_id = circuit_data["id"]
        assert float(circuit_data["md_kw"]) == pytest.approx(18.0), (
            f"MD esperado 18.0, obtenido {circuit_data['md_kw']}"
        )

        # ── Paso 3: Estación recalculada → max_demand_kw = 18 ──────────────
        r = client.get(f"/api/v1/stations/{station.id}", headers=auth_admin)
        assert r.status_code == 200
        demand_after_create = float(r.json()["max_demand_kw"])
        assert demand_after_create == pytest.approx(18.0), (
            f"max_demand_kw debería ser 18.0 tras crear circuito, obtenido {demand_after_create}"
        )

        # ── Paso 4: Cambiar estado del circuito a reserve_r ────────────────
        from datetime import date, timedelta
        new_expiry = (date.today() + timedelta(days=30)).isoformat()
        r = client.put(
            f"/api/v1/circuits/{circuit_id}/status",
            json={"status": "reserve_r", "reserve_expires_at": new_expiry},
            headers=auth_admin,
        )
        assert r.status_code == 200, f"Cambio de estado falló: {r.text}"
        assert r.json()["status"] == "reserve_r"

        # ── Paso 5: Audit log contiene CHANGE_CIRCUIT_STATUS ───────────────
        r = client.get(
            "/api/v1/audit",
            params={"entity_type": "circuit", "entity_id": circuit_id, "action": "CHANGE_CIRCUIT_STATUS"},
            headers=auth_admin,
        )
        assert r.status_code == 200
        logs = r.json()
        assert len(logs) >= 1, "Debe existir al menos un registro de auditoría de cambio de estado"
        actions = [log["action"] for log in logs]
        assert "CHANGE_CIRCUIT_STATUS" in actions, (
            f"No se encontró CHANGE_CIRCUIT_STATUS en audit logs: {actions}"
        )

        # ── Paso 6: Eliminar circuito ──────────────────────────────────────
        r = client.delete(f"/api/v1/circuits/{circuit_id}", headers=auth_admin)
        assert r.status_code == 200, f"Eliminar circuito falló: {r.text}"
        assert "eliminado" in r.json()["message"].lower()

        # ── Paso 7: Estación recalculada → max_demand_kw volvió a 0 ────────
        r = client.get(f"/api/v1/stations/{station.id}", headers=auth_admin)
        assert r.status_code == 200
        demand_after_delete = float(r.json()["max_demand_kw"])
        assert demand_after_delete == pytest.approx(0.0), (
            f"max_demand_kw debería ser 0 tras eliminar circuito, obtenido {demand_after_delete}"
        )

    def test_circuit_not_accessible_after_deletion(
        self, client, auth_admin, setup_station_and_bar
    ):
        """Verificación adicional: el circuito eliminado devuelve 404."""
        _, bar = setup_station_and_bar

        # Crear
        r = client.post(
            f"/api/v1/circuits/bar/{bar.id}",
            json={"denomination": "C-DEL", "name": "Para Eliminar", "pi_kw": 5.0, "fd": 1.0, "status": "operative_normal"},
            headers=auth_admin,
        )
        assert r.status_code == 201
        circuit_id = r.json()["id"]

        # Eliminar
        r = client.delete(f"/api/v1/circuits/{circuit_id}", headers=auth_admin)
        assert r.status_code == 200

        # Verificar que ya no existe
        r = client.get(f"/api/v1/circuits/{circuit_id}", headers=auth_admin)
        assert r.status_code == 404, "El circuito eliminado debe devolver 404"
