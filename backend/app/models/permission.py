from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Permission(Base):
    """
    Permiso granular que habilita o deshabilita una funcionalidad para un usuario Opersac.

    El sistema de permisos aplica exclusivamente a usuarios con rol 'opersac';
    los administradores tienen acceso total sin necesidad de registros en esta tabla.

    Cada fila representa la combinación de un usuario y una funcionalidad concreta.
    La restricción única sobre (user_id, feature_key) garantiza que no existan
    entradas duplicadas para el mismo par usuario-funcionalidad.

    Valores conocidos de `feature_key`:
        - 'view_stations': permite consultar el estado energético de las estaciones.
        - 'send_requests': permite enviar solicitudes de ampliación de carga.
        - 'view_reports': permite acceder a los reportes del sistema.
    """

    __tablename__ = "permissions"
    # Garantiza que cada usuario tenga como máximo un permiso por feature_key
    __table_args__ = (UniqueConstraint("user_id", "feature_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    # Identificador de la funcionalidad controlada (p.ej. 'view_stations', 'send_requests')
    feature_key: Mapped[str] = mapped_column(String(50), nullable=False)
    # True si el usuario tiene acceso habilitado; False si está explícitamente denegado
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="permissions")
