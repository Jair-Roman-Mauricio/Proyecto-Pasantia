from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.bar import Bar
from app.schemas.bar import BarResponse
from app.services.energy_calculator import EnergyCalculator

router = APIRouter(prefix="/bars", tags=["Bars"])


@router.get("/station/{station_id}", response_model=list[BarResponse])
def get_bars_by_station(
    station_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    bars = (
        db.query(Bar)
        .filter(Bar.station_id == station_id)
        .order_by(Bar.bar_type)
        .all()
    )
    return bars


@router.get("/{bar_id}", response_model=BarResponse)
def get_bar(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    bar = db.query(Bar).filter(Bar.id == bar_id).first()
    if not bar:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    return bar


@router.get("/{bar_id}/power-summary")
def get_bar_power_summary(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    calculator = EnergyCalculator(db)
    summary = calculator.get_bar_power_summary(bar_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    return summary
