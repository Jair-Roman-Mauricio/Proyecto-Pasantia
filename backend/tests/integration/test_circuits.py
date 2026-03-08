"""
Tests de Integración — Circuitos
===================================
Endpoint: /api/v1/bars/{bar_id}/circuits

Casos de prueba:
  TC-I06  Crear circuito válido calcula MD correctamente (PI=10, FD=0.8 → MD=8)
  TC-I07  Crear circuito sin campos obligatorios devuelve 422
  TC-I08  Crear circuito en reserva sin fecha de vencimiento devuelve 400
  TC-I09  Crear circuito UPS sin barras secundarias devuelve 400
  TC-I10  Crear circuito que excede capacidad sin force devuelve 400 con requires_force
  TC-I11  Crear circuito que excede capacidad con force=true devuelve 201
  TC-I12  Crear circuito recalcula max_demand_kw en la estación
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _circuit_url(bar_id: int) -> str:
    return f"/api/v1/bars/{bar_id}/circuits"


def _valid_payload(**overrides) -> dict:
    tomorrow = (date.today() + timedelta(days=30)).isoformat()
    base = {
        "denomination": "C-TEST-01",
        "name": "Circuito de prueba",
        "status": "operative_normal",
        "pi_kw": 10.0,
        "fd": 0.8,
        "is_ups": False,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# TC-I06: Crear circuito válido calcula MD = PI × FD correctamente
# ---------------------------------------------------------------------------

def test_create_circuit_calculates_md_correctly(client, auth_admin, bar):
    # Arrange
    payload = _valid_payload(pi_kw=10.0, fd=0.8)

    # Act
    response = client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert float(data["md_kw"]) == pytest.approx(8.0), (
        f"MD esperado 8.0, obtenido {data['md_kw']}"
    )


# ---------------------------------------------------------------------------
# TC-I07: Crear circuito sin campos obligatorios devuelve 422
# ---------------------------------------------------------------------------

def test_create_circuit_without_required_fields_returns_422(client, auth_admin, bar):
    # Arrange — falta 'denomination' y 'name'
    payload = {"pi_kw": 10.0, "fd": 0.8}

    # Act
    response = client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TC-I08: Crear circuito en reserva sin fecha de vencimiento devuelve 400
# ---------------------------------------------------------------------------

def test_create_reserve_circuit_without_expiry_date_returns_400(client, auth_admin, bar):
    # Arrange
    payload = _valid_payload(status="reserve_r")
    # No incluimos reserve_expires_at

    # Act
    response = client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 400
    assert "reserva" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# TC-I09: Crear circuito UPS sin barras secundarias devuelve 400
# ---------------------------------------------------------------------------

def test_create_ups_circuit_without_secondary_bars_returns_400(client, auth_admin, bar):
    # Arrange — is_ups=True pero sin secondary_bar_id ni tertiary_bar_id
    payload = _valid_payload(is_ups=True)

    # Act
    response = client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 400
    assert "UPS" in response.json()["detail"] or "barra" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# TC-I10: Exceder capacidad sin force devuelve 400 con requires_force=True
# ---------------------------------------------------------------------------

def test_create_circuit_exceeding_capacity_without_force_returns_400(client, auth_admin, bar):
    # Arrange — estación tiene 100 kW; pedimos 999 kW
    payload = _valid_payload(pi_kw=999.0, fd=1.0)

    # Act
    response = client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.get("requires_force") is True


# ---------------------------------------------------------------------------
# TC-I11: Exceder capacidad con force=True devuelve 201
# ---------------------------------------------------------------------------

def test_create_circuit_exceeding_capacity_with_force_returns_201(client, auth_admin, bar):
    # Arrange
    payload = _valid_payload(pi_kw=999.0, fd=1.0, force=True)

    # Act
    response = client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# TC-I12: Crear circuito recalcula max_demand_kw en la estación
# ---------------------------------------------------------------------------

def test_create_circuit_updates_station_max_demand(client, auth_admin, bar, station):
    # Arrange
    payload = _valid_payload(pi_kw=20.0, fd=1.0)

    # Act
    client.post(_circuit_url(bar.id), json=payload, headers=auth_admin)
    station_resp = client.get(f"/api/v1/stations/{station.id}", headers=auth_admin)

    # Assert
    updated_station = station_resp.json()
    assert float(updated_station["max_demand_kw"]) == pytest.approx(20.0), (
        "max_demand_kw de la estación debe actualizarse tras crear el circuito"
    )
