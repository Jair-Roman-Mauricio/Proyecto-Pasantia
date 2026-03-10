from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditLog(Base):
    """
    Registro de auditoría de las operaciones realizadas en el sistema.

    Cada vez que un usuario ejecuta una acción significativa (creación, edición
    o eliminación de entidades), se genera un registro en esta tabla. El objetivo
    es mantener una traza completa de la actividad para cumplimiento normativo
    y resolución de incidencias.

    El campo `action` describe la operación con un identificador legible,
    por ejemplo: 'CREAR_CIRCUITO', 'APROBAR_SOLICITUD', 'ELIMINAR_BARRA'.

    El campo `is_flagged` permite que un administrador marque registros
    sospechosos o relevantes para revisión especial, complementado por
    `flag_reason` que explica el motivo del marcado.

    Nota: los campos `user_role` y `user_name` se almacenan de forma
    desnormalizada para preservar el contexto histórico aunque el usuario
    sea modificado o eliminado posteriormente.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    # Rol del usuario en el momento de la acción (desnormalizado para preservar historial)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False)
    # Nombre del usuario en el momento de la acción (desnormalizado para preservar historial)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Fecha y hora exacta en que ocurrió la acción (indexado para consultas por rango)
    action_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    # Identificador de la operación realizada (p.ej. 'CREAR_CIRCUITO', 'APROBAR_SOLICITUD')
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # Tipo de entidad afectada (p.ej. 'Circuit', 'Station', 'Request')
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # ID de la entidad afectada; puede ser None si la acción no afecta a una entidad específica
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Información adicional de la operación en formato JSON (valores anteriores, nuevos, etc.)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Indica si el registro fue marcado para revisión especial por un administrador
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Motivo por el que se marcó el registro; solo se rellena cuando is_flagged=True
    flag_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
