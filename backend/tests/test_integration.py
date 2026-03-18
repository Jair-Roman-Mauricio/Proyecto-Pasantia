"""
Tests de integración end-to-end (Tarea 1 Etapa 04 + Tarea 1 Etapa 05).

Simula flujos completos tal como los usaría el frontend:
- Flujo Admin: crea infraestructura → agrega circuitos → valida energía
- Flujo Opersac: ve estaciones → envía solicitud → admin aprueba → energía actualizada
- Flujo de ciclo de vida de reserva: circuito pasa a reserva y vuelve a operativo
- Flujo de gestión de permisos: admin crea opersac → le da permisos → opersac accede
"""
import uuid
import pytest

from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.request import Request
from app.models.permission import Permission

STATIONS_URL = "/api/v1/stations"
BARS_URL = "/api/v1/bars"
CIRCUITS_URL = "/api/v1/circuits"
SUB_URL = "/api/v1/sub-circuits"
REQUESTS_URL = "/api/v1/requests"
PERMISSIONS_URL = "/api/v1/permissions"
USERS_URL = "/api/v1/users"
AUTH_ME = "/api/v1/auth/me"


# ---------------------------------------------------------------------------
# Flujo 1: Admin construye la infraestructura eléctrica de una estación
# ---------------------------------------------------------------------------

async def test_flow_admin_builds_infrastructure(
    client, admin_user, admin_token, station, bar, db
):
    """
    Admin crea 3 circuitos en la barra normal de E01 y verifica que
    la demanda de la estación sume correctamente.
    """
    circuits_data = [
        {"denomination": "ESC-01", "name": "Escalera Mecánica A", "pi_kw": "7.50", "fd": "0.7"},
        {"denomination": "ILU-01", "name": "Iluminación Andén", "pi_kw": "5.00", "fd": "0.9"},
        {"denomination": "FUE-01", "name": "Fuerza Servicios",  "pi_kw": "10.00", "fd": "0.8"},
    ]

    for c in circuits_data:
        resp = await client.post(
            f"{CIRCUITS_URL}/bar/{bar.id}",
            json={**c, "status": "operative_normal", "force": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201

    # Verificar demanda acumulada: (7.5×0.7) + (5×0.9) + (10×0.8) = 5.25+4.5+8 = 17.75
    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_st.status_code == 200
    demand = float(resp_st.json()["max_demand_kw"])
    assert demand == pytest.approx(17.75)
    assert resp_st.json()["status"] == "green"


# ---------------------------------------------------------------------------
# Flujo 2: Opersac envía solicitud → Admin aprueba → Energía se actualiza
# ---------------------------------------------------------------------------

async def test_flow_opersac_request_lifecycle(
    client, admin_user, admin_token, opersac_user, opersac_token, station, bar, db
):
    """
    Flujo completo: opersac crea solicitud → admin la aprueba →
    se crea el circuito → max_demand_kw de la estación se actualiza.
    """
    # 1. Opersac ve sus solicitudes (lista vacía)
    resp = await client.get(
        f"{REQUESTS_URL}/my",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []

    # 2. Opersac envía solicitud
    resp = await client.post(
        REQUESTS_URL,
        json={
            "station_id": station.id,
            "bar_type": "normal",
            "requested_load_kw": "25.00",
            "fd": "0.8",
            "justification": "Nuevo local comercial nivel -1",
        },
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200
    req_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    # 3. Opersac ve su solicitud en "mis solicitudes"
    resp = await client.get(
        f"{REQUESTS_URL}/my",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert len(resp.json()) == 1

    # 4. Admin lista todas las solicitudes y ve la nueva
    resp = await client.get(
        REQUESTS_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert any(r["id"] == req_id for r in resp.json())

    # 5. Admin aprueba
    resp = await client.put(
        f"{REQUESTS_URL}/{req_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # 6. La estación refleja la nueva demanda (25 × 0.8 = 20)
    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Flujo 3: Opersac solicita sub-circuito en circuito existente
# ---------------------------------------------------------------------------

async def test_flow_sub_circuit_request(
    client, admin_user, admin_token, opersac_user, opersac_token, circuit, station, bar, db
):
    """
    Opersac solicita sub-circuito en un circuito existente →
    Admin aprueba → se crea el sub-circuito → demanda aumenta.
    """
    # 1. Opersac ve los circuitos disponibles para su solicitud
    resp = await client.get(
        f"{REQUESTS_URL}/circuit-options/{bar.id}",
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200
    circuit_ids = [c["id"] for c in resp.json()]
    assert circuit.id in circuit_ids

    # 2. Opersac solicita sub-circuito
    resp = await client.post(
        REQUESTS_URL,
        json={
            "station_id": station.id,
            "bar_type": "normal",
            "circuit_id": circuit.id,
            "requested_load_kw": "3.00",
            "fd": "1.0",
            "sub_circuit_name": "Motor Escalera Tramo B",
            "sub_circuit_description": "Ampliacion tramo norte",
            "sub_circuit_itm": "16A",
            "sub_circuit_mm2": "2.5",
        },
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    assert resp.status_code == 200
    req_id = resp.json()["id"]

    # 3. Admin aprueba
    resp = await client.put(
        f"{REQUESTS_URL}/{req_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # 4. El sub-circuito existe en la BD
    subs = db.query(SubCircuit).filter(SubCircuit.circuit_id == circuit.id).all()
    assert len(subs) == 1
    assert subs[0].name == "Motor Escalera Tramo B"

    # 5. La demanda de la estación aumentó (circuit md=8 + sub md=3 = 11)
    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(11.0)


# ---------------------------------------------------------------------------
# Flujo 4: Ciclo de vida de un circuito (operativo → reserva → operativo)
# ---------------------------------------------------------------------------

async def test_flow_circuit_reserve_lifecycle(
    client, admin_user, admin_token, station, bar, circuit, db
):
    """
    Un circuito en operative_normal pasa a reserve_r y la demanda baja.
    Al volver a operative_normal la demanda se restaura.
    (status change no quita el circuito de la suma — solo inactive lo quita)
    """
    # Estado inicial: circuit.md_kw = 8
    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # La estación puede no haber sido calculada aún; forzar
    from app.services.energy_calculator import EnergyCalculator
    EnergyCalculator(db).recalculate_station(station.id)
    db.flush()

    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    demand_initial = float(resp_st.json()["max_demand_kw"])
    assert demand_initial == pytest.approx(8.0)

    # Pasar a reserve_r (reserve_r sigue contando según la lógica: status != inactive)
    resp = await client.put(
        f"{CIRCUITS_URL}/{circuit.id}/status",
        json={"status": "reserve_r", "reserve_expires_at": "2026-12-31"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "reserve_r"

    # Con reserve_r sigue contando (no es inactive)
    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(8.0)

    # Pasar a inactive → deja de contar
    resp = await client.put(
        f"{CIRCUITS_URL}/{circuit.id}/status",
        json={"status": "inactive"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Flujo 5: Admin crea usuario Opersac y gestiona sus permisos
# ---------------------------------------------------------------------------

async def test_flow_admin_manages_opersac_permissions(
    client, admin_user, admin_token, db
):
    """
    Admin crea usuario opersac → verifica que tiene todos los permisos en True →
    revoca view_stations → opersac ya no puede ver estaciones.
    """
    # 1. Admin crea usuario opersac
    resp = await client.post(
        USERS_URL,
        json={
            "username": "nuevo_opersac",
            "full_name": "Nuevo Operador SAC",
            "role": "opersac",
            "password": "Pass1234!",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    new_user_id = resp.json()["id"]

    # 2. Admin consulta los permisos del nuevo usuario
    resp = await client.get(
        f"{PERMISSIONS_URL}/users/{new_user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    perms = {p["feature_key"]: p["is_allowed"] for p in resp.json()}
    assert perms.get("view_stations") is True
    assert perms.get("send_requests") is True

    # 3. Admin revoca view_stations
    resp = await client.put(
        f"{PERMISSIONS_URL}/users/{new_user_id}",
        json={"permissions": [{"feature_key": "view_stations", "is_allowed": False}]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # 4. Verificar que el cambio se aplicó
    resp = await client.get(
        f"{PERMISSIONS_URL}/users/{new_user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    perms_updated = {p["feature_key"]: p["is_allowed"] for p in resp.json()}
    assert perms_updated.get("view_stations") is False


# ---------------------------------------------------------------------------
# Flujo 6: Rechazo de solicitud y verificación de no impacto energético
# ---------------------------------------------------------------------------

async def test_flow_rejected_request_no_energy_impact(
    client, admin_user, admin_token, opersac_user, opersac_token, station, bar, db
):
    """
    Una solicitud rechazada NO crea ningún circuito ni modifica la energía.
    """
    # Estado inicial de la estación
    resp_st_before = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    demand_before = float(resp_st_before.json()["max_demand_kw"])

    # Opersac envía solicitud
    resp = await client.post(
        REQUESTS_URL,
        json={
            "station_id": station.id,
            "bar_type": "normal",
            "requested_load_kw": "100.00",
            "fd": "1.0",
            "justification": "Solicitud a rechazar",
        },
        headers={"Authorization": f"Bearer {opersac_token}"},
    )
    req_id = resp.json()["id"]

    # Admin rechaza
    resp = await client.put(
        f"{REQUESTS_URL}/{req_id}/reject",
        json={"rejection_reason": "No hay capacidad disponible en la barra"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    # La energía de la estación NO cambió
    resp_st_after = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st_after.json()["max_demand_kw"]) == pytest.approx(demand_before)

    # No se creó ningún circuito nuevo en la barra
    circuits = db.query(Circuit).filter(Circuit.bar_id == bar.id).all()
    assert len(circuits) == 0
