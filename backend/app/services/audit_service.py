from app.subest_client import get_subest_client


class AuditService:
    def __init__(self):
        self.client = get_subest_client()

    def log(self, user, action: str, entity_type: str, entity_id=None, details: dict | None = None):
        self.client.table("audit_logs").insert({
            "user_id": str(user.id),
            "user_role": user.role,
            "user_name": user.full_name,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "details": details or {},
        }).execute()

    def flag_log(self, log_id: int, is_flagged: bool, reason: str | None = None) -> dict | None:
        result = self.client.table("audit_logs").update({
            "is_flagged": is_flagged,
            "flag_reason": reason,
        }).eq("id", log_id).execute()
        return result.data[0] if result.data else None
