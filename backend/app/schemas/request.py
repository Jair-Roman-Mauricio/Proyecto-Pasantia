"""
Schemas Pydantic para el recurso Solicitud de Ampliación (Request).

Define los modelos de creación, rechazo y respuesta de las solicitudes
de ampliación de carga que el personal Opersac eleva a los administradores.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


class RequestCreate(BaseModel):
    """
    Payload para crear una nueva solicitud de ampliación de carga.

    Usado por POST /requests.
    Permite solicitar la creación de un sub-circuito nuevo en un circuito
    existente o de un circuito nuevo en una barra de la estación indicada.
    El campo `user_id` se extrae automáticamente del token JWT.
    """

    station_id: int                                    # ID de la estación donde se solicita la ampliación
    # Tipo de barra destino: 'normal', 'emergency' o 'continuity'
    bar_type: str
    circuit_id: Optional[int] = None                  # ID del circuito existente (si se agrega un sub-circuito)
    local_item: Optional[str] = None                  # Local o ítem que originó la solicitud
    requested_load_kw: Decimal                         # Carga solicitada en kW
    fd: Decimal = Decimal("1.0")                      # Factor de demanda a aplicar (0.0–1.0)
    sub_circuit_name: Optional[str] = None            # Nombre del sub-circuito a crear (si aplica)
    sub_circuit_description: Optional[str] = None     # Descripción del sub-circuito a crear
    sub_circuit_itm: Optional[str] = None             # ITM del sub-circuito a crear
    sub_circuit_mm2: Optional[str] = None             # Sección del cable del sub-circuito en mm²
    justification: Optional[str] = None               # Justificación técnica de la solicitud


class RequestReject(BaseModel):
    """
    Payload para rechazar una solicitud de ampliación.

    Usado por POST /requests/{id}/reject.
    El motivo de rechazo es obligatorio para mantener trazabilidad.
    """

    rejection_reason: str  # Motivo del rechazo (obligatorio)


class RequestResponse(BaseModel):
    """
    Respuesta completa de una solicitud de ampliación de carga.

    Retornado por GET /requests y GET /requests/{id}.
    Incluye información desnormalizada de la estación, el circuito y el
    revisor para facilitar la visualización en el frontend.
    Los campos UUID se serializan como strings mediante el validador coerce_uuid.
    """

    id: int
    opersac_user_id: str                               # UUID del usuario Opersac solicitante (string)
    opersac_name: Optional[str] = None                # Nombre completo del solicitante (desnormalizado)
    station_id: int
    station_name: Optional[str] = None                # Nombre de la estación (desnormalizado)
    # Tipo de barra: 'normal', 'emergency' o 'continuity'
    bar_type: str
    circuit_id: Optional[int] = None                  # ID del circuito existente (si aplica)
    circuit_name: Optional[str] = None                # Nombre del circuito (desnormalizado)
    local_item: Optional[str] = None
    requested_load_kw: Decimal                         # Carga solicitada en kW
    fd: Decimal                                        # Factor de demanda aplicado
    sub_circuit_name: Optional[str] = None
    sub_circuit_description: Optional[str] = None
    sub_circuit_itm: Optional[str] = None
    sub_circuit_mm2: Optional[str] = None             # Sección del cable en mm²
    justification: Optional[str] = None
    # Estado de la solicitud: 'pending', 'approved' o 'rejected'
    status: str
    rejection_reason: Optional[str] = None            # Motivo de rechazo (solo cuando status='rejected')
    reviewed_by: Optional[str] = None                 # UUID del administrador revisor (string)
    reviewed_at: Optional[datetime] = None            # Fecha y hora de la revisión
    created_at: datetime
    updated_at: datetime

    @field_validator("opersac_user_id", "reviewed_by", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        """Convierte objetos UUID de SQLAlchemy a string para la serialización JSON."""
        return str(v) if v is not None else None

    class Config:
        from_attributes = True
