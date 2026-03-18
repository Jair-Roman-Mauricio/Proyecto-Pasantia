"""
Schemas Pydantic para el recurso Circuito (Circuit).

Define los modelos de creación, actualización, cambio de estado y respuesta
para los circuitos eléctricos que pertenecen a las barras de cada estación.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CircuitCreate(BaseModel):
    """
    Payload para crear un nuevo circuito en una barra eléctrica.

    Usado por POST /bars/{bar_id}/circuits.
    El campo `md_kw` se calcula automáticamente como pi_kw × fd si no se
    proporciona. El campo `force` permite omitir la validación de energía
    disponible en la barra (solo para administradores).
    """

    denomination: str                           # Denominación técnica del circuito (p.ej. "C-001")
    name: str                                   # Nombre descriptivo del circuito
    description: Optional[str] = None          # Descripción adicional del circuito
    local_item: Optional[str] = None           # Local o ítem al que corresponde el circuito
    pi_kw: Decimal                              # Potencia instalada en kW
    fd: Decimal = Decimal("1.0")               # Factor de demanda (0.0–1.0); por defecto 1.0
    md_kw: Optional[Decimal] = None            # Demanda máxima en kW; si None, se calcula: MD = pi_kw × fd
    status: str = "operative_normal"           # Estado inicial; valores válidos: ver CircuitStatus enum
    reserve_expires_at: Optional[date] = None  # Fecha de vencimiento si el circuito está en reserva
    is_ups: bool = False                        # True si el circuito está conectado a UPS
    secondary_bar_id: Optional[int] = None     # ID de barra secundaria (doble alimentación)
    tertiary_bar_id: Optional[int] = None      # ID de barra terciaria (triple alimentación)
    force: bool = False                         # Si True, omite la validación de energía disponible


class CircuitUpdate(BaseModel):
    """
    Payload para actualizar los datos técnicos de un circuito.

    Todos los campos son opcionales; solo se actualizan los proporcionados.
    Usado por PATCH /circuits/{id}.
    """

    denomination: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    local_item: Optional[str] = None
    pi_kw: Optional[Decimal] = None             # Potencia instalada en kW
    fd: Optional[Decimal] = None                # Factor de demanda (0.0–1.0)
    md_kw: Optional[Decimal] = None             # MD manual; si None, se recalcula: MD = pi_kw × fd


class CircuitStatusUpdate(BaseModel):
    """
    Payload para cambiar el estado operativo de un circuito.

    Usado por PATCH /circuits/{id}/status.
    El campo `reserve_expires_at` es obligatorio cuando el nuevo estado
    es 'reserve_r' o 'reserve_equipped_re'.
    """

    # Valores válidos: 'operative_normal', 'reserve_r', 'reserve_equipped_re', 'inactive'
    status: str
    reserve_expires_at: Optional[date] = None  # Fecha de vencimiento de la reserva


class CircuitResponse(BaseModel):
    """
    Respuesta completa de un circuito eléctrico.

    Retornado por GET /circuits y GET /circuits/{id}.
    Incluye IDs de barras secundaria y terciaria para circuitos con
    alimentación redundante, y las fechas de reserva cuando aplican.
    """

    id: int
    bar_id: int                                        # ID de la barra principal a la que pertenece
    secondary_bar_id: Optional[int] = None             # ID de la barra secundaria (si tiene)
    tertiary_bar_id: Optional[int] = None              # ID de la barra terciaria (si tiene)
    denomination: str                                  # Denominación técnica del circuito
    name: str
    description: Optional[str] = None
    local_item: Optional[str] = None
    pi_kw: Decimal                                     # Potencia instalada en kW
    fd: Decimal                                        # Factor de demanda aplicado
    md_kw: Decimal                                     # Demanda máxima calculada: MD = pi_kw × fd
    status: str                                        # Estado: 'operative_normal', 'reserve_r', etc.
    is_ups: bool                                       # True si está en barra de continuidad (UPS)
    reserve_since: Optional[date] = None               # Fecha en que entró en reserva
    reserve_expires_at: Optional[date] = None          # Fecha de vencimiento de la reserva
    client_last_contact: Optional[date] = None         # Último contacto registrado con el cliente
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
