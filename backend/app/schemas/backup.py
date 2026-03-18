"""
Schemas Pydantic para el recurso Backup.

Define los modelos de creación y respuesta de los snapshots de base de datos
que los administradores pueden generar para respaldar el estado del sistema.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BackupCreate(BaseModel):
    """
    Payload para generar un nuevo backup del sistema.

    Usado por POST /backups (solo administradores).
    El backend serializa todas las tablas operativas y, opcionalmente,
    la tabla de auditoría en un JSON que se almacena en la BD.
    """

    description: Optional[str] = None   # Descripción opcional del contexto del backup (p.ej. "Antes de migración v2")
    includes_audit: bool = True          # Si True, incluye la tabla audit_logs en el snapshot


class BackupResponse(BaseModel):
    """
    Respuesta de un registro de backup.

    Retornado por GET /backups y POST /backups.
    No incluye el campo `backup_data` (el JSON completo del snapshot) para
    evitar respuestas de gran tamaño; ese campo se descarga por separado.
    """

    id: int
    created_by: str                       # UUID del administrador que generó el backup (string)
    creator_name: Optional[str] = None   # Nombre completo del creador (desnormalizado)
    file_name: str                        # Nombre del archivo generado (p.ej. "backup_2026-03-18T12-00-00.json")
    description: Optional[str] = None    # Descripción del backup proporcionada al crearlo
    includes_audit: bool                  # True si el snapshot incluye la tabla audit_logs
    size_bytes: Optional[int] = None     # Tamaño del JSON serializado en bytes
    created_at: datetime

    class Config:
        from_attributes = True
