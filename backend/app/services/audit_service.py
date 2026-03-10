"""
Módulo de registro de auditoría del sistema.

Provee la clase AuditService, responsable de crear, consultar y marcar
registros de auditoría (audit logs) que documentan todas las acciones
relevantes realizadas por los usuarios sobre las entidades del sistema.
"""

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """
    Servicio de auditoría para el seguimiento de acciones de usuarios.

    Registra cada operación significativa (creación, modificación, eliminación)
    realizada sobre las entidades del sistema, asociándola al usuario que la
    ejecutó, su rol y los detalles del cambio. Permite consultar el historial
    de acciones y marcar registros sospechosos para revisión posterior.

    Attributes:
        db (Session): Sesión activa de SQLAlchemy utilizada para todas las
            operaciones de persistencia y consulta.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy inyectada desde el contexto
                de la solicitud HTTP.
        """
        self.db = db

    def log(
        self,
        user: User,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """
        Crea y persiste un nuevo registro de auditoría en la base de datos.

        Captura la identidad del usuario (id, rol y nombre completo) junto
        con la acción realizada y la entidad afectada, conformando un registro
        inmutable que facilita la trazabilidad y el cumplimiento normativo.

        Args:
            user (User): Objeto del usuario que realizó la acción. Se extraen
                ``user.id``, ``user.role`` y ``user.full_name`` para el registro.
            action (str): Código o descripción corta de la acción ejecutada
                (por ejemplo: ``'create'``, ``'update'``, ``'delete'``).
            entity_type (str): Tipo de entidad afectada (por ejemplo:
                ``'circuit'``, ``'station'``, ``'bar'``).
            entity_id (int | None): Identificador primario de la entidad
                afectada. Puede ser ``None`` cuando la acción no está
                vinculada a un registro específico.
            details (dict | None): Diccionario con información adicional del
                cambio, como los valores anteriores y nuevos de los campos
                modificados. Puede ser ``None`` si no aplica.

        Returns:
            AuditLog: Instancia del registro de auditoría recién creado,
                refrescada desde la base de datos con su ``id`` y
                ``action_date`` asignados automáticamente.
        """
        # Construir el objeto de auditoría con todos los campos del evento
        audit = AuditLog(
            user_id=user.id,
            user_role=user.role,
            user_name=user.full_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        # Agregar, confirmar y refrescar para obtener los valores generados por la BD
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
        """
        Consulta el historial de registros de auditoría con filtros opcionales.

        Permite filtrar los registros por tipo de entidad, entidad específica
        y/o usuario. Los resultados se ordenan por fecha de acción de forma
        descendente (más recientes primero) y admiten paginación mediante
        ``limit`` y ``offset``.

        Args:
            entity_type (str | None): Filtrar por tipo de entidad afectada.
                Si es ``None``, no se aplica este filtro.
            entity_id (int | None): Filtrar por identificador de entidad.
                Si es ``None``, no se aplica este filtro.
            user_id (int | None): Filtrar por identificador del usuario que
                realizó la acción. Si es ``None``, no se aplica este filtro.
            limit (int): Número máximo de registros a retornar. Por defecto 100.
            offset (int): Número de registros a omitir desde el inicio del
                resultado, utilizado para paginación. Por defecto 0.

        Returns:
            list[AuditLog]: Lista de instancias de ``AuditLog`` que cumplen
                los criterios de filtrado, ordenadas por fecha descendente.
        """
        # Iniciar la consulta base sobre la tabla de auditoría
        query = self.db.query(AuditLog)

        # Aplicar filtros únicamente cuando se proporcionan valores
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        # Ordenar por fecha descendente y aplicar paginación
        return (
            query.order_by(AuditLog.action_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def flag_log(self, log_id: int, is_flagged: bool, reason: str | None = None) -> AuditLog | None:
        """
        Marca o desmarca un registro de auditoría como sospechoso o de interés.

        Permite a los administradores señalar registros que requieren
        atención o investigación adicional, asociando opcionalmente un
        motivo textual a la marca.

        Args:
            log_id (int): Identificador primario del registro de auditoría
                a modificar.
            is_flagged (bool): ``True`` para marcar el registro; ``False``
                para quitar la marca.
            reason (str | None): Descripción del motivo por el que se marca
                el registro. Puede ser ``None`` si no se requiere justificación.

        Returns:
            AuditLog | None: El registro de auditoría actualizado y refrescado
                desde la base de datos. Retorna ``None`` si el registro con el
                ``log_id`` indicado no existe.
        """
        # Buscar el registro; si no existe, retornar None sin modificar nada
        log = self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not log:
            return None

        # Actualizar el estado de la marca y el motivo asociado
        log.is_flagged = is_flagged
        log.flag_reason = reason
        self.db.commit()
        self.db.refresh(log)
        return log
