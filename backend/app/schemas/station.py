"""
Schemas Pydantic para el recurso Estación (Station).

Define los modelos de entrada, salida y actualización parcial usados
por los endpoints de estaciones eléctricas de la Línea 1 del Metro.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class StationResponse(BaseModel):
    """
    Respuesta completa de una estación eléctrica.

    Retornado por los endpoints GET /stations y GET /stations/{id}.
    Incluye capacidades calculadas y el estado semafórico de energía disponible.
    """

    id: int
    code: str                              # Código único de la estación (p.ej. "E01")
    name: str                              # Nombre descriptivo de la estación
    order_index: int                       # Posición en la línea (de menor a mayor)
    transformer_capacity_kw: Decimal       # Capacidad nominal del transformador en kW
    max_demand_kw: Decimal                 # Suma de MD de todos los circuitos activos en kW
    available_power_kw: Decimal            # transformer_capacity_kw − max_demand_kw
    status: str                            # Estado semafórico: 'red', 'yellow' o 'green'
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StationUpdate(BaseModel):
    """
    Payload para actualizar los parámetros eléctricos de una estación.

    Todos los campos son opcionales; solo se actualizan los proporcionados.
    Usado por PATCH /stations/{id}.
    """

    transformer_capacity_kw: Optional[Decimal] = None  # Nueva capacidad del transformador en kW
    max_demand_kw: Optional[Decimal] = None             # Sobreescribe la demanda máxima calculada


class PowerSummary(BaseModel):
    """
    Resumen de potencia de una estación para vistas de dashboard.

    Versión simplificada de StationResponse orientada a paneles de monitoreo
    que solo requieren los datos energéticos, sin timestamps.
    """

    station_id: int
    station_name: str
    transformer_capacity_kw: Decimal   # Capacidad nominal del transformador en kW
    max_demand_kw: Decimal             # Demanda máxima total asignada en kW
    available_power_kw: Decimal        # Potencia libre disponible en kW
    status: str                        # Estado semafórico: 'red', 'yellow' o 'green'
