from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.circuit import Circuit
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationExtend
from app.utils.db_helpers import safe_commit

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="Listar notificaciones",
    description="Lista las notificaciones activas (no descartadas). Filtrable por `is_read` y `type`. Solo admin.",
    response_description="Lista de notificaciones ordenadas por fecha de creación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def get_notifications(
    is_read: bool | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(Notification).filter(Notification.is_dismissed == False)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if type:
        query = query.filter(Notification.type == type)
    return query.order_by(Notification.created_at.desc()).all()


@router.get(
    "/count",
    summary="Conteo de notificaciones no leídas",
    description="Retorna el número de notificaciones sin leer y no descartadas. Útil para mostrar el badge en la campana de notificaciones. Solo admin.",
    response_description="Objeto con la cantidad `unread_count`",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def get_unread_count(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    count = (
        db.query(Notification)
        .filter(Notification.is_read == False, Notification.is_dismissed == False)
        .count()
    )
    return {"unread_count": count}


@router.put(
    "/{notification_id}/read",
    summary="Marcar notificación como leída",
    description="Marca una notificación como leída (`is_read = true`). Solo admin.",
    response_description="Mensaje de confirmación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Notificación no encontrada"}},
)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif.is_read = True
    safe_commit(db)
    return {"message": "Marcado como leido"}


@router.put(
    "/{notification_id}/extend",
    summary="Extender fecha de una notificación",
    description="Extiende la fecha de vencimiento de una reserva sin contacto, indicando una nueva fecha en `extended_until`. También marca la notificación como leída. Solo admin.",
    response_description="Mensaje de confirmación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Notificación no encontrada"}},
)
def extend_notification(
    notification_id: int,
    data: NotificationExtend,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif.extended_until = data.extended_until
    notif.is_read = True
    safe_commit(db)
    return {"message": "Tiempo extendido"}


@router.put(
    "/{notification_id}/dismiss",
    summary="Descartar notificación",
    description="Descarta permanentemente una notificación (`is_dismissed = true`). No aparecerá en listados futuros. Solo admin.",
    response_description="Mensaje de confirmación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Notificación no encontrada"}},
)
def dismiss_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif.is_dismissed = True
    safe_commit(db)
    return {"message": "Notificacion descartada"}


@router.put(
    "/{notification_id}/resolve-reserve",
    summary="Resolver notificación de reserva vencida",
    description="Resuelve una notificación de tipo `reserve_no_contact`: pone el circuito asociado en estado `inactive` y descarta la notificación. Solo aplica a notificaciones de reservas sin contacto. Solo admin.",
    response_description="Mensaje de confirmación",
    responses={400: {"description": "La notificación no es de tipo reserve_no_contact"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Notificación no encontrada"}},
)
def resolve_reserve(
    notification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    if notif.type != "reserve_no_contact":
        raise HTTPException(status_code=400, detail="Solo aplica a notificaciones de reserva")
    if notif.circuit_id:
        circuit = db.query(Circuit).filter(Circuit.id == notif.circuit_id).first()
        if circuit:
            circuit.status = "inactive"
            circuit.reserve_since = None
            circuit.reserve_expires_at = None
    notif.is_dismissed = True
    safe_commit(db)
    return {"message": "Reserva eliminada"}
