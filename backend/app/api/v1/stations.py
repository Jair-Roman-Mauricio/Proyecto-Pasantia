from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin, check_permission
from app.models.user import User
from app.models.station import Station
from app.schemas.station import StationResponse, StationUpdate, PowerSummary
from app.services.energy_calculator import EnergyCalculator
from app.utils.db_helpers import safe_commit

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get(
    "",
    response_model=list[StationResponse],
    summary="Listar todas las estaciones",
    description="""
Retorna las 26 estaciones de la Línea 1 del Metro de Lima, ordenadas por `order_index` (de Villa El Salvador a Bayóvar).

Cada estación incluye su estado energético actual:
- `green` — Capacidad suficiente (> 20% disponible)
- `yellow` — Capacidad ajustada (< 20% disponible)
- `red` — Sobrecargada (demanda supera capacidad)

**Requiere permiso:** `view_stations`
""",
    response_description="Lista de estaciones ordenadas de sur a norte",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permiso view_stations no habilitado"},
    },
)
def get_stations(db: Session = Depends(get_db), _: User = Depends(check_permission("view_stations"))):
    stations = db.query(Station).order_by(Station.order_index).all()
    return stations


@router.get(
    "/{station_id}",
    response_model=StationResponse,
    summary="Obtener una estación por ID",
    description="Retorna los datos completos de una estación específica incluyendo su estado energético actual. **Requiere permiso:** `view_stations`",
    response_description="Datos de la estación solicitada",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permiso view_stations no habilitado"},
        404: {"description": "Estación no encontrada"},
    },
)
def get_station(
    station_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_stations")),
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    return station


@router.get(
    "/{station_id}/power-summary",
    response_model=PowerSummary,
    summary="Resumen de potencia de una estación",
    description="""
Retorna el resumen energético de una estación:
- `transformer_capacity_kw` — Capacidad total del transformador en kW
- `max_demand_kw` — Demanda máxima actual (suma de MD de todos los circuitos activos)
- `available_power_kw` — Potencia disponible = capacidad - demanda
- `status` — Estado: `green` / `yellow` / `red`

**Requiere permiso:** `view_stations`
""",
    response_description="Resumen de capacidad, demanda y disponibilidad de la estación",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permiso view_stations no habilitado"},
        404: {"description": "Estación no encontrada"},
    },
)
def get_power_summary(
    station_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_stations")),
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    return PowerSummary(
        station_id=station.id,
        station_name=station.name,
        transformer_capacity_kw=station.transformer_capacity_kw,
        max_demand_kw=station.max_demand_kw,
        available_power_kw=station.available_power_kw,
        status=station.status,
    )


@router.put(
    "/{station_id}",
    response_model=StationResponse,
    summary="Actualizar capacidad del transformador",
    description="""
Actualiza la capacidad del transformador de una estación en kW.
Tras la actualización, se **recalcula automáticamente** la energía disponible y el estado (`green`/`yellow`/`red`).

Solo accesible por administradores.
""",
    response_description="Datos de la estación con los valores recalculados",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Estación no encontrada"},
    },
)
def update_station(
    station_id: int,
    data: StationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")

    if data.transformer_capacity_kw is not None:
        station.transformer_capacity_kw = data.transformer_capacity_kw

    safe_commit(db)

    # Recalculate energy
    calculator = EnergyCalculator(db)
    station = calculator.recalculate_station(station_id)
    return station
