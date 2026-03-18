from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Servicio para registrar y consultar el log de auditoría del sistema.

    Cada acción relevante (crear/editar/eliminar circuitos, aprobar solicitudes,
    cambios de estado, etc.) genera una entrada en la tabla ``audit_logs`` con
    el usuario responsable, la entidad afectada y los detalles del cambio.
    """

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user: User,
        action: str,
        entity_type: str,
        entity_id: int | str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Registra una acción en el log de auditoría.

        Args:
            user: Usuario que realizó la acción.
            action: Nombre de la acción (ej: ``"create_circuit"``, ``"approve_request"``).
            entity_type: Tipo de entidad afectada (ej: ``"circuit"``, ``"station"``).
            entity_id: ID de la entidad afectada (int o UUID string). Opcional.
            details: Diccionario con información adicional del cambio (valores
                anteriores, nuevos, etc.). Opcional.

        Returns:
            La entrada ``AuditLog`` recién creada y persistida.
        """
        audit = AuditLog(
            user_id=user.id,
            user_role=user.role,
            user_name=user.full_name,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get_logs(
        self,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        user_id=None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Consulta entradas del log de auditoría con filtros opcionales.

        Los filtros se combinan con AND. Si no se especifica ninguno, devuelve
        las 100 entradas más recientes.

        Args:
            entity_type: Filtrar por tipo de entidad (ej: ``"circuit"``).
            entity_id: Filtrar por ID de entidad específica.
            user_id: Filtrar por UUID del usuario que realizó la acción.
            limit: Número máximo de registros a devolver (defecto 100).
            offset: Número de registros a saltar para paginación.

        Returns:
            Lista de ``AuditLog`` ordenados por fecha descendente.
        """
        query = self.db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.filter(AuditLog.entity_id == str(entity_id))
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        return (
            query.order_by(AuditLog.action_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def flag_log(self, log_id: int, is_flagged: bool, reason: str | None = None) -> AuditLog | None:
        """Marca o desmarca una entrada del log como flagged (sospechosa/revisada).

        Args:
            log_id: ID de la entrada a marcar.
            is_flagged: ``True`` para marcar, ``False`` para desmarcar.
            reason: Motivo del flag (requerido al marcar, opcional al desmarcar).

        Returns:
            La entrada ``AuditLog`` actualizada, o ``None`` si no existe.
        """
        log = self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not log:
            return None
        log.is_flagged = is_flagged
        log.flag_reason = reason
        self.db.commit()
        self.db.refresh(log)
        return log
