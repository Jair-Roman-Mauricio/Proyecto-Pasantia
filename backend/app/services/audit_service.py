from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user: User,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        audit = AuditLog(
            user_id=user.id,
            user_role=user.role,
            user_name=user.full_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get_logs(
        self,
        entity_type: str | None = None,
        entity_id: int | None = None,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        query = self.db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return (
            query.order_by(AuditLog.action_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def flag_log(self, log_id: int, is_flagged: bool, reason: str | None = None) -> AuditLog | None:
        log = self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not log:
            return None
        log.is_flagged = is_flagged
        log.flag_reason = reason
        self.db.commit()
        self.db.refresh(log)
        return log
