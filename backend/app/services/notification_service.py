from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.notification import Notification


def _has_active_notification(db: Session, circuit_id: int, today: date) -> bool:
    """Retorna True si ya existe una notificacion reserve_no_contact activa para este circuito."""
    return (
        db.query(Notification)
        .filter(
            Notification.circuit_id == circuit_id,
            Notification.type == "reserve_no_contact",
            Notification.is_dismissed == False,
        )
        .filter(
            (Notification.extended_until == None)
            | (Notification.extended_until > today)
        )
        .first()
        is not None
    )


def _make_message(name: str, expires_at: date, today: date) -> str:
    days_overdue = (today - expires_at).days
    if days_overdue <= 0:
        return (
            f"La reserva del circuito {name} vence hoy ({expires_at}). "
            f"Puede extender el plazo o eliminar la reserva."
        )
    return (
        f"La reserva del circuito {name} venció hace {days_overdue} día(s) (fecha límite: {expires_at}). "
        f"Puede extender el plazo o eliminar la reserva."
    )


def check_expiring_reserves(db: Session) -> None:
    today = date.today()

    # ── Caso 1: Circuitos con reserve_expires_at <= hoy ──────────────────────
    circuits = (
        db.query(Circuit)
        .options(joinedload(Circuit.bar))
        .filter(
            Circuit.status.in_(["reserve_r", "reserve_equipped_re"]),
            Circuit.reserve_expires_at.isnot(None),
            Circuit.reserve_expires_at <= today,
        )
        .all()
    )

    for circuit in circuits:
        try:
            if _has_active_notification(db, circuit.id, today):
                continue
            name = circuit.name or circuit.denomination
            bar = circuit.bar
            station_id = bar.station_id if bar else None
            db.add(
                Notification(
                    circuit_id=circuit.id,
                    station_id=station_id,
                    type="reserve_no_contact",
                    message=_make_message(name, circuit.reserve_expires_at, today),
                )
            )
        except Exception:
            continue

    # ── Caso 2: Sub-circuitos con reserve_expires_at <= hoy ──────────────────
    sub_circuits = (
        db.query(SubCircuit)
        .options(joinedload(SubCircuit.circuit).joinedload(Circuit.bar))
        .filter(
            SubCircuit.status.in_(["reserve_r", "reserve_equipped_re"]),
            SubCircuit.reserve_expires_at.isnot(None),
            SubCircuit.reserve_expires_at <= today,
        )
        .all()
    )

    for sub in sub_circuits:
        try:
            if _has_active_notification(db, sub.circuit_id, today):
                continue
            name = sub.name
            circuit = sub.circuit
            bar = circuit.bar if circuit else None
            station_id = bar.station_id if bar else None
            db.add(
                Notification(
                    circuit_id=sub.circuit_id,
                    station_id=station_id,
                    type="reserve_no_contact",
                    message=_make_message(f"sub-circuito {name}", sub.reserve_expires_at, today),
                )
            )
        except Exception:
            continue

    # ── Caso 3: Notificaciones con extended_until == hoy → crear nueva ────────
    expiring_extended = (
        db.query(Notification)
        .filter(
            Notification.type == "reserve_no_contact",
            Notification.extended_until == today,
            Notification.is_dismissed == False,
        )
        .all()
    )

    for notif in expiring_extended:
        try:
            if not notif.circuit_id:
                continue
            circuit = (
                db.query(Circuit)
                .options(joinedload(Circuit.bar))
                .filter(Circuit.id == notif.circuit_id)
                .first()
            )
            if circuit and circuit.status in ("reserve_r", "reserve_equipped_re"):
                notif.is_dismissed = True
                name = circuit.name or circuit.denomination
                bar = circuit.bar
                station_id = bar.station_id if bar else None
                db.add(
                    Notification(
                        circuit_id=circuit.id,
                        station_id=station_id,
                        type="reserve_no_contact",
                        message=(
                            f"La extensión de reserva del circuito {name} venció hoy ({today}). "
                            f"Puede extender nuevamente o eliminar la reserva."
                        ),
                    )
                )
        except Exception:
            continue

    try:
        db.commit()
    except Exception:
        db.rollback()
