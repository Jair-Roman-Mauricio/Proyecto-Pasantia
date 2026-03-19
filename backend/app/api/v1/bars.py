from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import check_permission, require_admin
from app.models.user import User
from app.models.bar import Bar
from app.schemas.bar import BarResponse, BarUpdate
from app.utils.db_helpers import safe_commit
from app.services.energy_calculator import EnergyCalculator

router = APIRouter(prefix="/bars", tags=["Bars"])


@router.get(
    "/station/{station_id}",
    response_model=list[BarResponse],
    summary="Listar barras de una estación",
    description="""
Retorna las barras eléctricas de la estación indicada. Cada estación tiene 3 barras:

| Tipo | Descripción |
|------|-------------|
| `normal` | Barra principal de distribución |
| `emergency` | Barra de emergencia (generador / UPS general) |
| `continuity` | Barra de continuidad (sistemas críticos) |

**Requiere permiso:** `view_stations`
""",
    response_description="Lista de barras de la estación ordenadas por tipo",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permiso view_stations no habilitado"},
    },
)
def get_bars_by_station(
    station_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_stations")),
):
    # Orden presentacional: normal → emergency → continuity
    bar_type_order = case(
        (Bar.bar_type == "normal", 1),
        (Bar.bar_type == "emergency", 2),
        (Bar.bar_type == "continuity", 3),
        else_=4,
    )
    bars = (
        db.query(Bar)
        .filter(Bar.station_id == station_id)
        .order_by(bar_type_order)
        .all()
    )
    return bars


@router.get(
    "/{bar_id}",
    response_model=BarResponse,
    summary="Obtener una barra por ID",
    description="Retorna los datos de una barra eléctrica específica. **Requiere permiso:** `view_stations`",
    response_description="Datos de la barra solicitada",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permiso view_stations no habilitado"},
        404: {"description": "Barra no encontrada"},
    },
)
def get_bar(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_stations")),
):
    bar = db.query(Bar).filter(Bar.id == bar_id).first()
    if not bar:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    return bar


@router.get(
    "/{bar_id}/power-summary",
    summary="Resumen de potencia de una barra",
    description="""
Retorna el resumen energético de una barra eléctrica específica:
- Capacidad total de la barra (kW y A)
- Demanda máxima acumulada de todos sus circuitos activos
- Potencia disponible restante

**Requiere permiso:** `view_stations`
""",
    response_description="Resumen de capacidad y demanda de la barra",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permiso view_stations no habilitado"},
        404: {"description": "Barra no encontrada"},
    },
)
def get_bar_power_summary(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_stations")),
):
    calculator = EnergyCalculator(db)
    summary = calculator.get_bar_power_summary(bar_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    return summary


@router.put(
    "/{bar_id}/capacity",
    response_model=BarResponse,
    summary="Actualizar capacidad del tablero",
    description="Actualiza la capacidad máxima en kW y A de una barra eléctrica. Solo admin.",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Barra no encontrada"},
    },
)
def update_bar_capacity(
    bar_id: int,
    data: BarUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    bar = db.query(Bar).filter(Bar.id == bar_id).first()
    if not bar:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    bar.capacity_kw = data.capacity_kw
    bar.capacity_a = data.capacity_a
    safe_commit(db)
    db.refresh(bar)
    return bar
