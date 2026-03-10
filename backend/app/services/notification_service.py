"""
Módulo de generación automática de notificaciones del sistema.

Contiene la lógica para detectar circuitos y sub-circuitos en estado de
reserva cuyo plazo ha vencido sin que se haya registrado contacto con el
cliente, y para generar las notificaciones correspondientes en la base
de datos. Este módulo es invocado periódicamente por un job programado.
"""

from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.notification import Notification


def _has_active_notification(db: Session, circuit_id: int, today: date) -> bool:
    """
    Verifica si ya existe una notificación activa de tipo 'reserve_no_contact'
    para el circuito indicado.

    Evita duplicar notificaciones cuando el job se ejecuta varias veces en
    el mismo día o cuando la reserva sigue vencida en ejecuciones posteriores.
    Una notificación se considera activa si no ha sido descartada
    (``is_dismissed = False``) y su extensión, si existe, aún no ha vencido.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        circuit_id (int): Identificador del circuito a verificar.
        today (date): Fecha actual utilizada para comparar ``extended_until``.

    Returns:
        bool: ``True`` si ya existe al menos una notificación activa para
            el circuito; ``False`` en caso contrario.
    """
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
    """
    Construye el texto de la notificación según si la reserva vence hoy o ya venció.

    Args:
        name (str): Nombre o denominación del circuito o sub-circuito.
        expires_at (date): Fecha en la que vence o venció la reserva.
        today (date): Fecha actual para calcular los días de atraso.

    Returns:
        str: Mensaje descriptivo listo para almacenar en el modelo
            ``Notification``. Indica si la reserva vence hoy o cuántos
            días lleva vencida, e invita al operador a extender o eliminar
            la reserva.
    """
    # Calcular cuántos días han pasado desde el vencimiento (negativo si es hoy)
    days_overdue = (today - expires_at).days
    if days_overdue <= 0:
        # La reserva vence exactamente hoy
        return (
            f"La reserva del circuito {name} vence hoy ({expires_at}). "
            f"Puede extender el plazo o eliminar la reserva."
        )
    # La reserva ya venció hace uno o más días
    return (
        f"La reserva del circuito {name} venció hace {days_overdue} día(s) (fecha límite: {expires_at}). "
        f"Puede extender el plazo o eliminar la reserva."
    )


def check_expiring_reserves(db: Session) -> None:
    """
    Detecta reservas vencidas y genera notificaciones automáticas del sistema.

    Ejecuta tres casos de detección de forma secuencial:

    **Caso 1 — Circuitos con reserva vencida:**
        Consulta circuitos en estado ``reserve_r`` o ``reserve_equipped_re``
        cuya fecha ``reserve_expires_at`` sea menor o igual a hoy. Por cada
        uno crea una notificación de tipo ``reserve_no_contact`` si no existe
        ya una notificación activa.

    **Caso 2 — Sub-circuitos con reserva vencida:**
        Igual que el caso 1 pero sobre la tabla ``sub_circuits``. La
        notificación queda asociada al circuito padre del sub-circuito.

    **Caso 3 — Extensiones que vencen hoy:**
        Busca notificaciones de tipo ``reserve_no_contact`` cuya
        ``extended_until`` sea exactamente hoy. Descarta la notificación
        vigente y crea una nueva para alertar que la extensión también
        ha vencido.

    Al finalizar, persiste todos los cambios en la base de datos. Si ocurre
    una excepción durante el commit, realiza un rollback para mantener la
    consistencia de los datos.

    Args:
        db (Session): Sesión activa de SQLAlchemy. No se cierra ni se
            gestiona su ciclo de vida dentro de esta función.

    Returns:
        None
    """
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
            # Omitir si ya existe una notificación activa para este circuito
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
            # Continuar con el siguiente circuito ante cualquier error puntual
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
            # Omitir si ya existe una notificación activa para el circuito padre
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
            # Continuar con el siguiente sub-circuito ante cualquier error puntual
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
            # Ignorar notificaciones huérfanas sin circuito asociado
            if not notif.circuit_id:
                continue
            circuit = (
                db.query(Circuit)
                .options(joinedload(Circuit.bar))
                .filter(Circuit.id == notif.circuit_id)
                .first()
            )
            if circuit and circuit.status in ("reserve_r", "reserve_equipped_re"):
                # Descartar la notificación extendida que acaba de vencer
                notif.is_dismissed = True
                name = circuit.name or circuit.denomination
                bar = circuit.bar
                station_id = bar.station_id if bar else None
                # Crear una nueva notificación indicando que la extensión también venció
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
            # Continuar con la siguiente notificación ante cualquier error puntual
            continue

    try:
        # Persistir todas las nuevas notificaciones generadas en esta ejecución
        db.commit()
    except Exception:
        # Revertir la transacción completa si el commit falla
        db.rollback()
