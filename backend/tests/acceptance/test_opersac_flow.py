"""
Tests de Aceptación — Flujo completo rol Opersac
=================================================
Endpoints: /api/v1/auth, /api/v1/requests, /api/v1/notifications

Casos de prueba:
  TC-A02  Opersac crea solicitud, Admin aprueba, se verifica la solicitud aprobada

Patrón: Arrange → Act (pasos secuenciales) → Assert por etapa
"""

import pytest
from decimal import Decimal

from app.models.station import Station
from app.models.bar import Bar
from app.models.permission import Permission


# ---------------------------------------------------------------------------
# Fixtures locales: estación, barra, usuario opersac con permiso
# ---------------------------------------------------------------------------

@pytest.fixture
def station_for_request(db_session):
    """Estación con barra de tipo 'normal' lista para recibir solicitudes."""
    station = Station(
        code="OPS01", name="Estacion Opersac Flow", order_index=60,
        transformer_capacity_kw=Decimal("500"), max_demand_kw=Decimal("0"),
        available_power_kw=Decimal("500"), status="green",
    )
    db_session.add(station)
    db_session.commit()

    bar = Bar(
        station_id=station.id, name="Barra Normal OPS", bar_type="normal",
        status="operative", capacity_kw=Decimal("500"), capacity_a=Decimal("800"),
    )
    db_session.add(bar)
    db_session.commit()
    db_session.refresh(station)
    db_session.refresh(bar)
    return station, bar


@pytest.fixture
def opersac_with_permission(db_session, opersac_user):
    """Usuario opersac con permiso send_requests habilitado."""
    perm = Permission(
        user_id=opersac_user.id,
        feature_key="send_requests",
        is_allowed=True,
    )
    db_session.add(perm)
    db_session.commit()
    return opersac_user


# ---------------------------------------------------------------------------
# TC-A02: Flujo completo opersac → solicitud → admin aprueba
# ---------------------------------------------------------------------------

class TestOpersacRequestFlow:
    """
    TC-A02: Opersac crea solicitud de ampliación, Admin la aprueba.

    Pasos:
      1. POST /requests          → opersac crea solicitud (status=pending)
      2. GET /requests/my        → opersac ve su solicitud en estado pending
      3. GET /requests           → admin ve la solicitud pendiente
      4. PUT /requests/{id}/approve → admin aprueba la solicitud
      5. GET /requests/{id}      → solicitud en estado approved (verificar como admin)
    """

    def test_opersac_creates_request_admin_approves(
        self,
        client,
        auth_admin,
        auth_opersac,
        db_session,
        admin_user,
        opersac_with_permission,
        station_for_request,
    ):
        station, bar = station_for_request

        # ── Paso 1: Opersac crea solicitud ────────────────────────────────
        r = client.post(
            "/api/v1/requests",
            json={
                "station_id": station.id,
                "bar_type": "normal",
                "local_item": "Local 101",
                "requested_load_kw": 15.0,
                "fd": 0.85,
                "justification": "Ampliación de carga para nueva maquinaria",
            },
            headers=auth_opersac,
        )
        assert r.status_code == 200, f"Crear solicitud falló: {r.text}"
        request_data = r.json()
        request_id = request_data["id"]
        assert request_data["status"] == "pending", (
            f"La solicitud debe iniciar en 'pending', estado actual: {request_data['status']}"
        )
        assert request_data["station_id"] == station.id

        # ── Paso 2: Opersac ve su solicitud en /my ────────────────────────
        r = client.get("/api/v1/requests/my", headers=auth_opersac)
        assert r.status_code == 200
        my_requests = r.json()
        assert len(my_requests) >= 1, "El opersac debe ver al menos una solicitud propia"
        my_ids = [req["id"] for req in my_requests]
        assert request_id in my_ids, f"La solicitud {request_id} no aparece en /requests/my"

        # ── Paso 3: Admin ve la solicitud en la lista global ──────────────
        r = client.get("/api/v1/requests", headers=auth_admin)
        assert r.status_code == 200
        all_requests = r.json()
        all_ids = [req["id"] for req in all_requests]
        assert request_id in all_ids, f"La solicitud {request_id} no aparece en GET /requests"

        # Verificar que está en pending desde la perspectiva del admin
        target = next(req for req in all_requests if req["id"] == request_id)
        assert target["status"] == "pending"

        # ── Paso 4: Admin aprueba la solicitud ────────────────────────────
        r = client.put(
            f"/api/v1/requests/{request_id}/approve",
            headers=auth_admin,
        )
        assert r.status_code == 200, f"Aprobar solicitud falló: {r.text}"
        approved_data = r.json()
        assert approved_data["status"] == "approved", (
            f"La solicitud debe pasar a 'approved', estado actual: {approved_data['status']}"
        )
        assert approved_data["reviewed_by"] == admin_user.id

        # ── Paso 5: Verificar solicitud aprobada en lista global ──────────
        r = client.get("/api/v1/requests", headers=auth_admin)
        assert r.status_code == 200
        updated_requests = r.json()
        updated_target = next(
            (req for req in updated_requests if req["id"] == request_id), None
        )
        assert updated_target is not None, "La solicitud aprobada debe seguir visible"
        assert updated_target["status"] == "approved"

    def test_opersac_cannot_see_all_requests(
        self, client, auth_opersac, opersac_with_permission
    ):
        """Opersac no puede acceder a GET /requests (solo admin)."""
        r = client.get("/api/v1/requests", headers=auth_opersac)
        assert r.status_code == 403, (
            f"Opersac no debe acceder a GET /requests, obtuvo: {r.status_code}"
        )

    def test_opersac_cannot_approve_requests(
        self,
        client,
        auth_opersac,
        auth_admin,
        db_session,
        opersac_with_permission,
        station_for_request,
    ):
        """Opersac no puede aprobar solicitudes — solo admin puede."""
        station, _ = station_for_request

        # Opersac crea una solicitud
        r = client.post(
            "/api/v1/requests",
            json={
                "station_id": station.id,
                "bar_type": "normal",
                "requested_load_kw": 5.0,
                "fd": 1.0,
                "justification": "Test permisos",
            },
            headers=auth_opersac,
        )
        assert r.status_code == 200
        request_id = r.json()["id"]

        # Opersac intenta aprobar → debe fallar con 403
        r = client.put(
            f"/api/v1/requests/{request_id}/approve",
            headers=auth_opersac,
        )
        assert r.status_code == 403, (
            f"Opersac no debe poder aprobar solicitudes, obtuvo: {r.status_code}"
        )

    def test_request_without_send_requests_permission_is_forbidden(
        self, client, auth_opersac, db_session, station_for_request
    ):
        """
        Opersac sin permiso send_requests no puede crear solicitudes.
        (Este fixture NO agrega el permiso — usa auth_opersac sin opersac_with_permission)
        """
        station, _ = station_for_request

        r = client.post(
            "/api/v1/requests",
            json={
                "station_id": station.id,
                "bar_type": "normal",
                "requested_load_kw": 5.0,
                "fd": 1.0,
            },
            headers=auth_opersac,
        )
        assert r.status_code == 403, (
            f"Sin permiso send_requests debe devolver 403, obtuvo: {r.status_code}"
        )
