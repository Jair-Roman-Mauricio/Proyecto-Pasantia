from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_admin
from app.subest_client import get_subest_client
from app.schemas.notification import NotificationResponse, NotificationExtend

router = APIRouter(prefix="/notifications", tags=["Notifications"])

VALID_TYPES = ["reserve_no_contact", "negative_energy"]


@router.get("", response_model=list[NotificationResponse])
def get_notifications(is_read: bool | None = None, type: str | None = None, _=Depends(require_admin)):
    client = get_subest_client()
    query = client.table("notifications").select("*").eq("is_dismissed", False).in_("type", VALID_TYPES)
    if is_read is not None:
        query = query.eq("is_read", is_read)
    if type:
        query = query.eq("type", type)
    result = query.order("created_at", desc=True).execute()
    return result.data


@router.get("/count")
def get_unread_count(_=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("notifications").select("id").eq("is_read", False).eq("is_dismissed", False).in_("type", VALID_TYPES).execute()
    return {"unread_count": len(result.data)}


@router.put("/{notification_id}/read")
def mark_as_read(notification_id: int, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("notifications").select("id").eq("id", notification_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    client.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
    return {"message": "Marcado como leido"}


@router.put("/{notification_id}/extend")
def extend_notification(notification_id: int, data: NotificationExtend, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("notifications").select("*").eq("id", notification_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif = result.data[0]

    client.table("notifications").update({
        "extended_until": data.extended_until.isoformat(),
        "is_read": True,
    }).eq("id", notification_id).execute()

    if notif.get("circuit_id"):
        client.table("circuits").update({"reserve_expires_at": data.extended_until.isoformat()}).eq("id", notif["circuit_id"]).execute()

    return {"message": "Tiempo extendido"}


@router.put("/{notification_id}/dismiss")
def dismiss_notification(notification_id: int, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("notifications").select("id").eq("id", notification_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    client.table("notifications").update({"is_dismissed": True}).eq("id", notification_id).execute()
    return {"message": "Notificacion descartada"}


@router.put("/{notification_id}/resolve-reserve")
def resolve_reserve(notification_id: int, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("notifications").select("*").eq("id", notification_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notif = result.data[0]

    if notif["type"] != "reserve_no_contact":
        raise HTTPException(status_code=400, detail="Solo aplica a notificaciones de reserva")

    if notif.get("circuit_id"):
        client.table("circuits").update({
            "status": "operative_normal",
            "reserve_since": None,
            "reserve_expires_at": None,
        }).eq("id", notif["circuit_id"]).execute()

    client.table("notifications").update({"is_dismissed": True}).eq("id", notification_id).execute()
    return {"message": "Reserva eliminada"}
