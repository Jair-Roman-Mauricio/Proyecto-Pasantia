"""
Tests de validación de flujos energéticos (Tarea 4, Etapa 04).

Verifica que el EnergyCalculator actualice correctamente max_demand_kw,
available_power_kw y el estado (green/yellow/red) de una estación ante
cambios en circuitos y sub-circuitos.
"""
import pytest
from decimal import Decimal

from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.station import Station
from app.services.energy_calculator import EnergyCalculator

CIRCUITS_URL = "/api/v1/circuits"
SUB_URL = "/api/v1/sub-circuits"
STATIONS_URL = "/api/v1/stations"


# ---------------------------------------------------------------------------
# Pruebas directas del EnergyCalculator (sin HTTP)
# ---------------------------------------------------------------------------

def test_empty_station_is_green(db, station, bar):
    """Estación sin circuitos tiene demanda 0 y estado green."""
    calc = EnergyCalculator(db)
    result = calc.recalculate_station(station.id)
    assert result.max_demand_kw == Decimal("0")
    assert result.status == "green"


def test_station_becomes_yellow_below_20_percent(db, station, bar):
    """
    Con transformer_capacity_kw=500, yellow se activa cuando
    available_power_kw < 100 (20% de 500).
    Agregamos un circuito con md_kw=420 → disponible=80 → yellow.
    """
    circuit = Circuit(
        bar_id=bar.id, denomination="C-YEL", name="Circuito Yellow",
        pi_kw=420, fd=1.0, md_kw=420, status="operative_normal",
    )
    db.add(circuit)
    db.flush()

    calc = EnergyCalculator(db)
    result = calc.recalculate_station(station.id)

    assert result.max_demand_kw == Decimal("420")
    assert result.available_power_kw == Decimal("80")
    assert result.status == "yellow"


def test_station_becomes_red_when_overloaded(db, station, bar):
    """Demanda > capacidad → estado red."""
    circuit = Circuit(
        bar_id=bar.id, denomination="C-RED", name="Circuito Red",
        pi_kw=600, fd=1.0, md_kw=600, status="operative_normal",
    )
    db.add(circuit)
    db.flush()

    calc = EnergyCalculator(db)
    result = calc.recalculate_station(station.id)

    assert result.available_power_kw < 0
    assert result.status == "red"


def test_inactive_circuit_not_counted(db, station, bar):
    """Circuitos con status='inactive' NO se suman a la demanda."""
    circuit = Circuit(
        bar_id=bar.id, denomination="C-INACT", name="Inactivo",
        pi_kw=300, fd=1.0, md_kw=300, status="inactive",
    )
    db.add(circuit)
    db.flush()

    calc = EnergyCalculator(db)
    result = calc.recalculate_station(station.id)

    assert result.max_demand_kw == Decimal("0")
    assert result.status == "green"


def test_sub_circuit_operative_adds_to_demand(db, station, bar, circuit):
    """Sub-circuito en operative_normal suma su md_kw a la demanda total."""
    sub = SubCircuit(
        circuit_id=circuit.id, name="Sub Op", pi_kw=50, fd=1.0, md_kw=50,
        status="operative_normal",
    )
    db.add(sub)
    db.flush()

    calc = EnergyCalculator(db)
    result = calc.recalculate_station(station.id)

    # circuit.md_kw=8 + sub.md_kw=50
    assert result.max_demand_kw == Decimal("58")


def test_sub_circuit_in_reserve_not_counted(db, station, bar, circuit):
    """Sub-circuito en reserve_r NO suma a la demanda."""
    sub = SubCircuit(
        circuit_id=circuit.id, name="Sub Reserva", pi_kw=50, fd=1.0, md_kw=50,
        status="reserve_r",
    )
    db.add(sub)
    db.flush()

    calc = EnergyCalculator(db)
    result = calc.recalculate_station(station.id)

    # Solo el circuito padre: md_kw=8
    assert result.max_demand_kw == Decimal("8")


def test_removing_circuit_updates_demand(db, station, bar):
    """Eliminar un circuito y recalcular reduce la demanda."""
    circuit = Circuit(
        bar_id=bar.id, denomination="C-DEL", name="A Eliminar",
        pi_kw=100, fd=1.0, md_kw=100, status="operative_normal",
    )
    db.add(circuit)
    db.flush()

    calc = EnergyCalculator(db)
    result_before = calc.recalculate_station(station.id)
    assert result_before.max_demand_kw == Decimal("100")

    db.delete(circuit)
    db.flush()

    result_after = calc.recalculate_station(station.id)
    assert result_after.max_demand_kw == Decimal("0")
    assert result_after.status == "green"


def test_check_capacity_sufficient(db, station, bar):
    """check_capacity retorna can_add=True cuando hay potencia suficiente."""
    calc = EnergyCalculator(db)
    result = calc.check_capacity(bar.id, Decimal("100"))
    assert result["can_add"] is True
    assert result["available_after"] == pytest.approx(400.0)


def test_check_capacity_exceeded(db, station, bar):
    """check_capacity retorna can_add=False cuando la nueva carga supera la disponible."""
    calc = EnergyCalculator(db)
    result = calc.check_capacity(bar.id, Decimal("600"))
    assert result["can_add"] is False
    assert "Excede" in result["message"]


def test_check_capacity_nonexistent_bar(db):
    """check_capacity con barra inexistente retorna can_add=False."""
    calc = EnergyCalculator(db)
    result = calc.check_capacity(99999, Decimal("10"))
    assert result["can_add"] is False


# ---------------------------------------------------------------------------
# Validación de flujos energéticos vía API
# ---------------------------------------------------------------------------

async def test_api_create_circuit_updates_station_demand(
    client, admin_user, admin_token, station, bar, db
):
    """Crear un circuito vía API debe actualizar max_demand_kw de la estación."""
    resp = await client.post(
        f"{CIRCUITS_URL}/bar/{bar.id}",
        json={
            "denomination": "C-API",
            "name": "Via API",
            "pi_kw": "50.00",
            "fd": "1.0",
            "status": "operative_normal",
            "force": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201

    # Consultar la estación y verificar actualización
    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(50.0)


async def test_api_delete_circuit_reduces_demand(
    client, admin_user, admin_token, station, bar, circuit, db
):
    """Eliminar un circuito vía API debe reducir max_demand_kw."""
    # Primero forzamos un recalculo para que la estación tenga el circuito contado
    calc = EnergyCalculator(db)
    calc.recalculate_station(station.id)
    db.flush()

    resp = await client.delete(
        f"{CIRCUITS_URL}/{circuit.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(0.0)


async def test_api_approve_request_updates_station_energy(
    client, admin_user, admin_token, opersac_user, station, bar, db
):
    """Aprobar una solicitud debe crear un circuito y actualizar la energía."""
    from app.models.request import Request

    req = Request(
        opersac_user_id=opersac_user.id,
        station_id=station.id,
        bar_type="normal",
        requested_load_kw=75,
        fd=1.0,
        status="pending",
    )
    db.add(req)
    db.flush()

    resp = await client.put(
        f"/api/v1/requests/{req.id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert float(resp_st.json()["max_demand_kw"]) == pytest.approx(75.0)


async def test_station_status_turns_red_via_api(
    client, admin_user, admin_token, station, bar, db
):
    """Agregar un circuito que supera la capacidad cambia el estado a red."""
    # Estación tiene 500 kW de capacidad, agregamos 600 con force=True
    resp = await client.post(
        f"{CIRCUITS_URL}/bar/{bar.id}",
        json={
            "denomination": "C-OVR",
            "name": "Sobrecarga",
            "pi_kw": "600.00",
            "fd": "1.0",
            "status": "operative_normal",
            "force": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201

    resp_st = await client.get(
        f"{STATIONS_URL}/{station.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_st.json()["status"] == "red"
