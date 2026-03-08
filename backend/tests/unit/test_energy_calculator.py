"""
Tests Unitarios — EnergyCalculator
===================================
Módulo: app/services/energy_calculator.py

Casos de prueba:
  TC-U01  MD correcto con un circuito (PI=10, FD=0.8 → MD=8)
  TC-U02  Estado verde cuando hay más del 20% disponible
  TC-U03  Estado amarillo cuando hay menos del 20% disponible
  TC-U04  Estado rojo cuando la demanda supera la capacidad
  TC-U05  Circuitos inactivos no cuentan en el MD total
  TC-U06  Sub-circuitos operativos se suman al MD
  TC-U07  check_capacity permite agregar si hay espacio suficiente
  TC-U08  check_capacity rechaza si se excede la capacidad disponible

Convención de nombres: test_<acción>_<condición>_<resultado_esperado>
Patrón: Arrange → Act → Assert (AAA)
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.station import Station
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.services.energy_calculator import EnergyCalculator


# ---------------------------------------------------------------------------
# Fixtures locales: BD aislada con datos mínimos
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _make_station(db, capacity_kw: float) -> Station:
    s = Station(
        code="S01", name="Test", order_index=1,
        transformer_capacity_kw=Decimal(str(capacity_kw)),
        max_demand_kw=Decimal("0"), available_power_kw=Decimal(str(capacity_kw)),
        status="green",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _make_bar(db, station_id: int, capacity_kw: float = 200.0) -> Bar:
    b = Bar(
        station_id=station_id, name="Barra A", bar_type="principal",
        status="operative", capacity_kw=Decimal(str(capacity_kw)), capacity_a=Decimal("400"),
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def _make_circuit(db, bar_id: int, pi_kw: float, fd: float, status: str = "operative_normal") -> Circuit:
    c = Circuit(
        bar_id=bar_id, denomination="C1", name="Circuito Test",
        pi_kw=Decimal(str(pi_kw)), fd=Decimal(str(fd)),
        md_kw=Decimal(str(round(pi_kw * fd, 2))),
        status=status,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_sub_circuit(db, circuit_id: int, pi_kw: float, fd: float, status: str = "operative_normal") -> SubCircuit:
    sc = SubCircuit(
        circuit_id=circuit_id, denomination="SC1", name="Sub Test",
        pi_kw=Decimal(str(pi_kw)), fd=Decimal(str(fd)),
        md_kw=Decimal(str(round(pi_kw * fd, 2))),
        status=status,
    )
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc


# ---------------------------------------------------------------------------
# TC-U01: MD correcto con un circuito (PI=10, FD=0.8 → MD=8)
# ---------------------------------------------------------------------------

def test_md_calculation_single_circuit_returns_correct_value(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    _make_circuit(db, bar.id, pi_kw=10, fd=0.8)

    calc = EnergyCalculator(db)

    # Act
    result = calc.recalculate_station(station.id)

    # Assert
    assert result.max_demand_kw == Decimal("8.00"), (
        f"MD esperado 8.00, obtenido {result.max_demand_kw}"
    )


# ---------------------------------------------------------------------------
# TC-U02: Estado verde — más del 20% disponible (50 kW usados de 100)
# ---------------------------------------------------------------------------

def test_status_green_when_demand_below_80_percent(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    _make_circuit(db, bar.id, pi_kw=50, fd=1.0)  # MD=50, disponible=50%

    calc = EnergyCalculator(db)

    # Act
    result = calc.recalculate_station(station.id)

    # Assert
    assert result.status == "green"


# ---------------------------------------------------------------------------
# TC-U03: Estado amarillo — menos del 20% disponible (85 kW usados de 100)
# ---------------------------------------------------------------------------

def test_status_yellow_when_demand_above_80_percent(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    _make_circuit(db, bar.id, pi_kw=85, fd=1.0)  # MD=85, disponible=15%

    calc = EnergyCalculator(db)

    # Act
    result = calc.recalculate_station(station.id)

    # Assert
    assert result.status == "yellow"


# ---------------------------------------------------------------------------
# TC-U04: Estado rojo — demanda supera la capacidad (110 kW de 100)
# ---------------------------------------------------------------------------

def test_status_red_when_demand_exceeds_capacity(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    _make_circuit(db, bar.id, pi_kw=110, fd=1.0)  # MD=110, excede 100

    calc = EnergyCalculator(db)

    # Act
    result = calc.recalculate_station(station.id)

    # Assert
    assert result.status == "red"
    assert result.available_power_kw < Decimal("0")


# ---------------------------------------------------------------------------
# TC-U05: Circuitos inactivos no cuentan en el MD
# ---------------------------------------------------------------------------

def test_md_excludes_inactive_circuits(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    _make_circuit(db, bar.id, pi_kw=20, fd=1.0, status="operative_normal")
    _make_circuit(db, bar.id, pi_kw=50, fd=1.0, status="inactive")  # debe ignorarse

    calc = EnergyCalculator(db)

    # Act
    result = calc.recalculate_station(station.id)

    # Assert
    assert result.max_demand_kw == Decimal("20.00"), (
        "El circuito inactivo no debe sumarse al MD"
    )


# ---------------------------------------------------------------------------
# TC-U06: Sub-circuitos operativos se suman al MD
# ---------------------------------------------------------------------------

def test_md_includes_operative_sub_circuits(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    circuit = _make_circuit(db, bar.id, pi_kw=10, fd=1.0)  # MD=10
    _make_sub_circuit(db, circuit.id, pi_kw=5, fd=1.0)     # MD adicional=5
    _make_sub_circuit(db, circuit.id, pi_kw=3, fd=1.0)     # MD adicional=3

    calc = EnergyCalculator(db)

    # Act
    result = calc.recalculate_station(station.id)

    # Assert
    assert result.max_demand_kw == Decimal("18.00"), (
        "MD debe incluir circuito (10) + sub-circuitos (5+3)"
    )


# ---------------------------------------------------------------------------
# TC-U07: check_capacity permite agregar si hay espacio suficiente
# ---------------------------------------------------------------------------

def test_check_capacity_allows_when_space_available(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)
    # La estación tiene 100 kW disponibles, queremos agregar 30

    calc = EnergyCalculator(db)

    # Act
    result = calc.check_capacity(bar.id, Decimal("30"))

    # Assert
    assert result["can_add"] is True
    assert result["available_after"] == pytest.approx(70.0)


# ---------------------------------------------------------------------------
# TC-U08: check_capacity rechaza si se excede la capacidad disponible
# ---------------------------------------------------------------------------

def test_check_capacity_rejects_when_exceeds_available(db):
    # Arrange
    station = _make_station(db, capacity_kw=100)
    bar = _make_bar(db, station.id)

    calc = EnergyCalculator(db)

    # Act
    result = calc.check_capacity(bar.id, Decimal("999"))

    # Assert
    assert result["can_add"] is False
    assert "Excede" in result["message"]
