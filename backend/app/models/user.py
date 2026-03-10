from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    Representa un usuario del sistema de gestión energética.

    Existen dos roles con comportamientos distintos:
        - 'admin': acceso total al sistema sin restricciones de permisos.
        - 'opersac': acceso limitado según los registros de la tabla `permissions`.
          Solo puede operar sobre las funcionalidades que tenga habilitadas.

    La contraseña nunca se almacena en texto plano; el campo `password_hash`
    contiene el resultado del algoritmo de hashing configurado en la capa de
    seguridad de la aplicación.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # Hash de la contraseña; nunca almacenar la contraseña en texto plano
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Rol del usuario: 'admin' (acceso total) u 'opersac' (acceso según permisos)
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
