from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.station import Station
from app.schemas.station import StationResponse, StationUpdate, PowerSummary
from app.services.energy_calculator import EnergyCalculator

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=list[StationResponse])
def get_stations(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    stations = db.query(Station).order_by(Station.order_index).all()
    return stations


@router.get("/{station_id}", response_model=StationResponse)
def get_station(
    station_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    return station


@router.get("/{station_id}/power-summary", response_model=PowerSummary)
def get_power_summary(
    station_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
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


@router.put("/{station_id}", response_model=StationResponse)
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

    db.commit()

    # Recalculate energy
    calculator = EnergyCalculator(db)
    station = calculator.recalculate_station(station_id)
    return station
