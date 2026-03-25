from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import check_permission, require_admin
from app.subest_client import get_subest_client
from app.schemas.bar import BarResponse, BarUpdate
from app.services.energy_calculator import EnergyCalculator

router = APIRouter(prefix="/bars", tags=["Bars"])

BAR_ORDER = {"normal": 1, "emergency": 2, "continuity": 3}


@router.get("/station/{station_id}", response_model=list[BarResponse])
def get_bars_by_station(station_id: int, _=Depends(check_permission("view_stations"))):
    client = get_subest_client()
    result = client.table("bars").select("*").eq("station_id", station_id).execute()
    bars = sorted(result.data, key=lambda b: BAR_ORDER.get(b["bar_type"], 4))
    return bars


@router.get("/{bar_id}", response_model=BarResponse)
def get_bar(bar_id: int, _=Depends(check_permission("view_stations"))):
    client = get_subest_client()
    result = client.table("bars").select("*").eq("id", bar_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    return result.data[0]


@router.get("/{bar_id}/power-summary")
def get_bar_power_summary(bar_id: int, _=Depends(check_permission("view_stations"))):
    calculator = EnergyCalculator()
    summary = calculator.get_bar_power_summary(bar_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    return summary


@router.put("/{bar_id}/capacity", response_model=BarResponse)
def update_bar_capacity(bar_id: int, data: BarUpdate, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("bars").select("*").eq("id", bar_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    updated = client.table("bars").update({
        "capacity_kw": float(data.capacity_kw),
        "capacity_a": float(data.capacity_a),
    }).eq("id", bar_id).execute()
    return updated.data[0]
