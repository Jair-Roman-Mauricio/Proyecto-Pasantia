from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, require_admin, check_permission
from app.subest_client import get_subest_client
from app.schemas.station import StationResponse, StationUpdate, PowerSummary
from app.services.energy_calculator import EnergyCalculator

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=list[StationResponse])
def get_stations(_=Depends(check_permission("view_stations"))):
    client = get_subest_client()
    result = client.table("stations").select("*").order("order_index").execute()
    return result.data


@router.get("/{station_id}", response_model=StationResponse)
def get_station(station_id: int, _=Depends(check_permission("view_stations"))):
    client = get_subest_client()
    result = client.table("stations").select("*").eq("id", station_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    return result.data[0]


@router.get("/{station_id}/power-summary", response_model=PowerSummary)
def get_power_summary(station_id: int, _=Depends(check_permission("view_stations"))):
    client = get_subest_client()
    result = client.table("stations").select("*").eq("id", station_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    s = result.data[0]
    return PowerSummary(
        station_id=s["id"],
        station_name=s["name"],
        transformer_capacity_kw=s["transformer_capacity_kw"],
        max_demand_kw=s["max_demand_kw"],
        available_power_kw=s["available_power_kw"],
        status=s["status"],
    )


@router.put("/{station_id}", response_model=StationResponse)
def update_station(station_id: int, data: StationUpdate, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("stations").select("*").eq("id", station_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")

    if data.transformer_capacity_kw is not None:
        client.table("stations").update({"transformer_capacity_kw": float(data.transformer_capacity_kw)}).eq("id", station_id).execute()

    calculator = EnergyCalculator()
    updated = calculator.recalculate_station(station_id)
    return updated
