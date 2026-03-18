"""
Modelo SQLAlchemy para la tabla de backups del sistema.

Cada registro representa un snapshot completo de la base de datos serializado
en JSON, generado por un administrador para permitir la restauración del
estado operativo del sistema ante errores o pérdida de datos.
"""

from datetime import datetime, timezone
from typing import Optional

import uuid

from sqlalchemy import String, Integer, Boolean, BigInteger, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Backup(Base):
    """
    Representa un snapshot completo de la base de datos en formato JSON.

    Cada registro de esta tabla captura el estado íntegro del sistema en un
    momento dado, serializando todas las tablas relevantes dentro del campo
    `backup_data`. Los backups permiten restaurar la base de datos a un estado
    anterior en caso de error operativo o pérdida de datos.

    El campo `includes_audit` indica si el snapshot incluye también la tabla
    de auditoría (`audit_logs`), que puede omitirse para reducir el tamaño del
    archivo cuando solo interesa el estado operativo del sistema.
    """

    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Usuario administrador que generó el backup
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Serialización JSON de todas las tablas incluidas en el snapshot
    backup_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Indica si el backup incluye la tabla audit_logs además de los datos operativos
    includes_audit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Tamaño del JSON serializado en bytes; útil para estimar el costo de almacenamiento
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    creator = relationship("User", foreign_keys=[created_by])
