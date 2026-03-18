"""
Schemas Pydantic para el recurso Sub-Circuito (SubCircuit).

Define los modelos de creación, actualización, cambio de estado y respuesta
para los sub-circuitos que dependen de un circuito padre.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SubCircuitCreate(BaseModel):
    """
    Payload para crear un sub-circuito dentro de un circuito existente.

    Usado por POST /circuits/{circuit_id}/sub-circuits.
    El campo `md_kw` se calcula automáticamente como pi_kw × fd si no se
    proporciona.
    """

    name: str                                   # Nombre descriptivo del sub-circuito
    description: Optional[str] = None          # Descripción técnica adicional
    itm: Optional[str] = None                  # Referencia al Interruptor Termomagnético (ITM)
    mm2: Optional[str] = None                  # Sección del cable en mm² (p.ej. "6", "10", "16")
    pi_kw: Decimal                              # Potencia instalada en kW
    fd: Decimal = Decimal("1.0")               # Factor de demanda (0.0–1.0); por defecto 1.0
    md_kw: Optional[Decimal] = None            # Demanda máxima en kW; si None, se calcula: MD = pi_kw × fd
    status: str = "operative_normal"           # Estado inicial; valores válidos: ver CircuitStatus enum
    reserve_expires_at: Optional[date] = None  # Fecha de vencimiento si el sub-circuito está en reserva


class SubCircuitUpdate(BaseModel):
    """
    Payload para actualizar los datos técnicos de un sub-circuito.

    Todos los campos son opcionales; solo se actualizan los proporcionados.
    Usado por PATCH /sub-circuits/{id}.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    itm: Optional[str] = None                  # Referencia al ITM asociado
    mm2: Optional[str] = None                  # Sección del cable en mm²
    pi_kw: Optional[Decimal] = None            # Potencia instalada en kW
    fd: Optional[Decimal] = None               # Factor de demanda (0.0–1.0)
    md_kw: Optional[Decimal] = None            # MD manual; si None, se recalcula: MD = pi_kw × fd


class SubCircuitResponse(BaseModel):
    """
    Respuesta completa de un sub-circuito.

    Retornado por GET /sub-circuits y GET /sub-circuits/{id}.
    Incluye los campos técnicos del sub-circuito y las fechas de reserva
    cuando el estado es 'reserve_r' o 'reserve_equipped_re'.
    """

    id: int
    circuit_id: int                              # ID del circuito padre al que pertenece
    name: str
    description: Optional[str] = None
    itm: Optional[str] = None                   # Referencia al Interruptor Termomagnético
    mm2: Optional[str] = None                   # Sección del cable en mm²
    pi_kw: Decimal                               # Potencia instalada en kW
    fd: Decimal                                  # Factor de demanda aplicado
    md_kw: Decimal                               # Demanda máxima calculada: MD = pi_kw × fd
    status: str                                  # Estado: 'operative_normal', 'reserve_r', etc.
    reserve_since: Optional[date] = None         # Fecha en que entró en reserva
    reserve_expires_at: Optional[date] = None    # Fecha de vencimiento de la reserva
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubCircuitStatusUpdate(BaseModel):
    """
    Payload para cambiar el estado operativo de un sub-circuito.

    Usado por PATCH /sub-circuits/{id}/status.
    El campo `reserve_expires_at` es obligatorio cuando el nuevo estado
    es 'reserve_r' o 'reserve_equipped_re'.
    """

    # Valores válidos: 'operative_normal', 'reserve_r', 'reserve_equipped_re', 'inactive'
    status: str
    reserve_expires_at: Optional[date] = None  # Fecha de vencimiento de la reserva
