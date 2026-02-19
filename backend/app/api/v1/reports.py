import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.station import Station
from app.models.request import Request
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/demand-evolution")
def get_demand_evolution(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    stations = db.query(Station).order_by(Station.order_index).all()
    data = []
    for station in stations:
        data.append({
            "station_id": station.id,
            "station_name": station.name,
            "station_code": station.code,
            "transformer_capacity_kw": float(station.transformer_capacity_kw),
            "max_demand_kw": float(station.max_demand_kw),
            "available_power_kw": float(station.available_power_kw),
            "status": station.status,
        })
    return data


@router.get("/requests-per-station")
def get_requests_per_station(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(
        Request.station_id,
        Station.name,
        Request.status,
        func.count(Request.id).label("count"),
    ).join(Station, Request.station_id == Station.id)

    if start_date:
        query = query.filter(Request.created_at >= start_date)
    if end_date:
        query = query.filter(Request.created_at <= end_date)

    results = query.group_by(Request.station_id, Station.name, Request.status).all()

    data = {}
    for station_id, station_name, status, count in results:
        if station_name not in data:
            data[station_name] = {"station_id": station_id, "station_name": station_name, "pending": 0, "approved": 0, "rejected": 0}
        data[station_name][status] = count

    return list(data.values())


@router.get("/export/excel")
def export_reports_excel(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from openpyxl import Workbook

    wb = Workbook()

    # Sheet 1: Demand evolution
    ws1 = wb.active
    ws1.title = "Demanda Electrica"
    ws1.append(["Estacion", "Codigo", "Capacidad (kW)", "Demanda Max (kW)", "Disponible (kW)", "Estado"])

    stations = db.query(Station).order_by(Station.order_index).all()
    for s in stations:
        ws1.append([
            s.name,
            s.code,
            float(s.transformer_capacity_kw),
            float(s.max_demand_kw),
            float(s.available_power_kw),
            s.status,
        ])

    # Sheet 2: Requests per station
    ws2 = wb.create_sheet("Solicitudes por Estacion")
    ws2.append(["Estacion", "Pendientes", "Aprobadas", "Rechazadas", "Total"])

    station_requests = db.query(
        Station.name,
        func.count(Request.id).label("total"),
    ).outerjoin(Request, Station.id == Request.station_id).group_by(Station.name).all()

    for name, total in station_requests:
        ws2.append([name, 0, 0, 0, total or 0])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reportes.xlsx"},
    )
