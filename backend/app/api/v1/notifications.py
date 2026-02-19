from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationExtend

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
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


@router.get("/count")
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


@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif.is_read = True
    db.commit()
    return {"message": "Marcado como leido"}


@router.put("/{notification_id}/extend")
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
    db.commit()
    return {"message": "Tiempo extendido"}


@router.put("/{notification_id}/dismiss")
def dismiss_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif.is_dismissed = True
    db.commit()
    return {"message": "Notificacion descartada"}
