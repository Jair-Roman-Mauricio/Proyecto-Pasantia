from datetime import date
from app.subest_client import get_subest_client


def _make_message(name: str, expires_at, today: date) -> str:
    days_overdue = (today - expires_at).days if hasattr(expires_at, 'days') else 0
    if isinstance(expires_at, str):
        from datetime import datetime
        expires_at = datetime.strptime(expires_at, "%Y-%m-%d").date()
        days_overdue = (today - expires_at).days
    if days_overdue <= 0:
        return f"La reserva del circuito {name} vence hoy ({expires_at}). Puede extender el plazo o eliminar la reserva."
    return f"La reserva del circuito {name} venció hace {days_overdue} día(s) (fecha límite: {expires_at}). Puede extender el plazo o eliminar la reserva."


def _parse_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        from datetime import datetime
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _has_active_notification(client, circuit_id: int, today: date) -> bool:
    result = client.table("notifications").select("id,extended_until").eq("circuit_id", circuit_id).eq("type", "reserve_no_contact").eq("is_dismissed", False).execute()
    for n in result.data:
        ext = _parse_date(n.get("extended_until"))
        if ext is None or ext > today:
            return True
    return False


def check_expiring_reserves() -> None:
    client = get_subest_client()
    today = date.today()
    today_str = today.isoformat()

    # Case 1: circuits with expired reserve
    circuits = client.table("circuits").select("id,name,denomination,bar_id,reserve_expires_at").in_("status", ["reserve_r", "reserve_equipped_re"]).not_.is_("reserve_expires_at", "null").lte("reserve_expires_at", today_str).execute().data

    for circuit in circuits:
        try:
            if _has_active_notification(client, circuit["id"], today):
                continue
            name = circuit.get("name") or circuit.get("denomination") or str(circuit["id"])
            bar_result = client.table("bars").select("station_id").eq("id", circuit["bar_id"]).execute()
            station_id = bar_result.data[0]["station_id"] if bar_result.data else None
            expires_at = _parse_date(circuit["reserve_expires_at"])
            client.table("notifications").insert({
                "circuit_id": circuit["id"],
                "station_id": station_id,
                "type": "reserve_no_contact",
                "message": _make_message(name, expires_at, today),
            }).execute()
        except Exception:
            continue

    # Case 2: sub_circuits with expired reserve
    subs = client.table("sub_circuits").select("id,name,circuit_id,reserve_expires_at").in_("status", ["reserve_r", "reserve_equipped_re"]).not_.is_("reserve_expires_at", "null").lte("reserve_expires_at", today_str).execute().data

    for sub in subs:
        try:
            if _has_active_notification(client, sub["circuit_id"], today):
                continue
            circuit_result = client.table("circuits").select("bar_id").eq("id", sub["circuit_id"]).execute()
            station_id = None
            if circuit_result.data:
                bar_result = client.table("bars").select("station_id").eq("id", circuit_result.data[0]["bar_id"]).execute()
                if bar_result.data:
                    station_id = bar_result.data[0]["station_id"]
            expires_at = _parse_date(sub["reserve_expires_at"])
            client.table("notifications").insert({
                "circuit_id": sub["circuit_id"],
                "station_id": station_id,
                "type": "reserve_no_contact",
                "message": _make_message(f"sub-circuito {sub['name']}", expires_at, today),
            }).execute()
        except Exception:
            continue

    # Case 3: extended notifications expiring today
    expiring = client.table("notifications").select("id,circuit_id").eq("type", "reserve_no_contact").eq("extended_until", today_str).eq("is_dismissed", False).execute().data

    for notif in expiring:
        try:
            if not notif.get("circuit_id"):
                continue
            circuit_result = client.table("circuits").select("id,name,denomination,bar_id,status").eq("id", notif["circuit_id"]).execute()
            if not circuit_result.data:
                continue
            circuit = circuit_result.data[0]
            if circuit["status"] not in ("reserve_r", "reserve_equipped_re"):
                continue
            client.table("notifications").update({"is_dismissed": True}).eq("id", notif["id"]).execute()
            bar_result = client.table("bars").select("station_id").eq("id", circuit["bar_id"]).execute()
            station_id = bar_result.data[0]["station_id"] if bar_result.data else None
            name = circuit.get("name") or circuit.get("denomination") or str(circuit["id"])
            client.table("notifications").insert({
                "circuit_id": circuit["id"],
                "station_id": station_id,
                "type": "reserve_no_contact",
                "message": f"La extensión de reserva del circuito {name} venció hoy ({today}). Puede extender nuevamente o eliminar la reserva.",
            }).execute()
        except Exception:
            continue
