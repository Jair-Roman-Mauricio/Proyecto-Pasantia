"""
Tests de Integración — Notificaciones
=======================================
Endpoints: /api/v1/notifications

Casos de prueba:
  TC-I18  Marcar notificación como leída actualiza is_read=True
  TC-I19  Extender reserva actualiza reserve_expires_at en el circuito
  TC-I20  Eliminar reserva cambia estado del circuito a operative_normal
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models.notification import Notification
from app.models.circuit import Circuit
from app.models.bar import Bar
from app.models.station import Station


# ---------------------------------------------------------------------------
# Fixtures locales: notificación con circuito en reserva
# ---------------------------------------------------------------------------

@pytest.fixture
def reserve_circuit(db_session):
    """Circuito en estado reserve_r con fecha de reserva próxima a vencer."""
    station = Station(
        code="NT01", name="Estacion Notif", order_index=10,
        transformer_capacity_kw=Decimal("100"), max_demand_kw=Decimal("0"),
        available_power_kw=Decimal("100"), status="green",
    )
    db_session.add(station)
    db_session.commit()

    bar = Bar(
        station_id=station.id, name="Barra NT", bar_type="principal",
        status="operative", capacity_kw=Decimal("100"), capacity_a=Decimal("200"),
    )
    db_session.add(bar)
    db_session.commit()

    circuit = Circuit(
        bar_id=bar.id, denomination="C-RESERVA", name="Circuito Reserva",
        pi_kw=Decimal("10"), fd=Decimal("1.0"), md_kw=Decimal("10"),
        status="reserve_r",
        reserve_expires_at=date.today() + timedelta(days=5),
    )
    db_session.add(circuit)
    db_session.commit()
    db_session.refresh(circuit)
    return circuit


@pytest.fixture
def reserve_notification(db_session, reserve_circuit, admin_user):
    """Notificación de tipo reserve_no_contact asociada al circuito en reserva."""
    notif = Notification(
        type="reserve_no_contact",
        message="Reserva próxima a vencer sin contacto",
        station_id=reserve_circuit.bar.station_id if hasattr(reserve_circuit, 'bar') else 1,
        circuit_id=reserve_circuit.id,
        is_read=False,
        is_dismissed=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)
    return notif


# ---------------------------------------------------------------------------
# TC-I18: Marcar notificación como leída actualiza is_read=True
# ---------------------------------------------------------------------------

def test_mark_notification_as_read_updates_is_read(client, auth_admin, db_session, admin_user):
    # Arrange — crear notificación de prueba directamente en BD
    station = Station(
        code="NR01", name="Est Read", order_index=99,
        transformer_capacity_kw=Decimal("100"), max_demand_kw=Decimal("0"),
        available_power_kw=Decimal("100"), status="green",
    )
    db_session.add(station)
    db_session.commit()

    notif = Notification(
        type="negative_energy",
        message="Test notificación no leída",
        station_id=station.id,
        is_read=False,
        is_dismissed=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    # Act
    response = client.put(f"/api/v1/notifications/{notif.id}/read", headers=auth_admin)

    # Assert
    assert response.status_code == 200
    db_session.refresh(notif)
    assert notif.is_read is True


# ---------------------------------------------------------------------------
# TC-I19: Extender reserva actualiza reserve_expires_at en el circuito
# ---------------------------------------------------------------------------

def test_extend_reserve_updates_expiry_date_in_circuit(client, auth_admin, db_session, admin_user):
    # Arrange
    station = Station(
        code="NE01", name="Est Extend", order_index=98,
        transformer_capacity_kw=Decimal("100"), max_demand_kw=Decimal("0"),
        available_power_kw=Decimal("100"), status="green",
    )
    db_session.add(station)
    db_session.commit()

    bar = Bar(
        station_id=station.id, name="Barra EXT", bar_type="principal",
        status="operative", capacity_kw=Decimal("100"), capacity_a=Decimal("200"),
    )
    db_session.add(bar)
    db_session.commit()

    circuit = Circuit(
        bar_id=bar.id, denomination="C-EXT", name="Circuito Extend",
        pi_kw=Decimal("5"), fd=Decimal("1.0"), md_kw=Decimal("5"),
        status="reserve_r",
        reserve_expires_at=date.today() + timedelta(days=3),
    )
    db_session.add(circuit)
    db_session.commit()

    notif = Notification(
        type="reserve_no_contact",
        message="Reserva por extender",
        station_id=station.id,
        circuit_id=circuit.id,
        is_read=False,
        is_dismissed=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    new_date = (date.today() + timedelta(days=60)).isoformat()

    # Act
    response = client.put(
        f"/api/v1/notifications/{notif.id}/extend",
        json={"extended_until": new_date},
        headers=auth_admin,
    )

    # Assert
    assert response.status_code == 200
    db_session.refresh(circuit)
    assert circuit.reserve_expires_at.isoformat() == new_date


# ---------------------------------------------------------------------------
# TC-I20: Eliminar reserva cambia estado del circuito a operative_normal
# ---------------------------------------------------------------------------

def test_resolve_reserve_changes_circuit_status_to_operative(client, auth_admin, db_session, admin_user):
    # Arrange
    station = Station(
        code="NS01", name="Est Solve", order_index=97,
        transformer_capacity_kw=Decimal("100"), max_demand_kw=Decimal("0"),
        available_power_kw=Decimal("100"), status="green",
    )
    db_session.add(station)
    db_session.commit()

    bar = Bar(
        station_id=station.id, name="Barra SLV", bar_type="principal",
        status="operative", capacity_kw=Decimal("100"), capacity_a=Decimal("200"),
    )
    db_session.add(bar)
    db_session.commit()

    circuit = Circuit(
        bar_id=bar.id, denomination="C-SLV", name="Circuito Solve",
        pi_kw=Decimal("5"), fd=Decimal("1.0"), md_kw=Decimal("5"),
        status="reserve_r",
        reserve_expires_at=date.today() + timedelta(days=1),
    )
    db_session.add(circuit)
    db_session.commit()

    notif = Notification(
        type="reserve_no_contact",
        message="Reserva a eliminar",
        station_id=station.id,
        circuit_id=circuit.id,
        is_read=False,
        is_dismissed=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    # Act
    response = client.put(
        f"/api/v1/notifications/{notif.id}/resolve-reserve",
        headers=auth_admin,
    )

    # Assert
    assert response.status_code == 200
    db_session.refresh(circuit)
    assert circuit.status == "operative_normal"
