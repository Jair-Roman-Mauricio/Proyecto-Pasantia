import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class User(Base):
    """
    Perfil de usuario vinculado a Supabase Auth.

    La autenticación (contraseña, sesión, tokens) es gestionada por Supabase Auth.
    Este modelo almacena únicamente los datos de perfil y rol necesarios para
    la lógica de negocio de la aplicación.

    El campo `id` es el UUID asignado por Supabase Auth (auth.users.id),
    lo que permite validar tokens JWT de Supabase y recuperar el perfil
    en una sola consulta.

    Roles:
        - 'admin': acceso total al sistema sin restricciones de permisos.
        - 'opersac': acceso limitado según los registros de la tabla `permissions`.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    permissions = relationship("Permission", back_populates="user", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")
