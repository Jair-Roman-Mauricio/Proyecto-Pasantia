import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from decimal import Decimal

from app.database import get_db
from app.dependencies import require_admin, check_permission
from app.models.user import User
from app.models.station import Station
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.request import Request
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/demand-evolution")
def get_demand_evolution(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_reports")),
):
    stations = db.query(Station).order_by(Station.order_index).all()

    if not start_date and not end_date:
        # No filter: return current station values
        return [
            {
                "station_id": station.id,
                "station_name": station.name,
                "station_code": station.code,
                "transformer_capacity_kw": float(station.transformer_capacity_kw),
                "max_demand_kw": float(station.max_demand_kw),
                "available_power_kw": float(station.available_power_kw),
                "status": station.status,
            }
            for station in stations
        ]

    # With date filter: compute demand from circuits/sub-circuits created in the range
    data = []
    for station in stations:
        bar_ids = [b.id for b in db.query(Bar.id).filter(Bar.station_id == station.id).all()]
        total_md = Decimal("0")

        if bar_ids:
            circ_query = db.query(Circuit).filter(
                Circuit.bar_id.in_(bar_ids),
                Circuit.status != "inactive",
            )
            if start_date:
                circ_query = circ_query.filter(Circuit.created_at >= start_date)
            if end_date:
                circ_query = circ_query.filter(Circuit.created_at <= end_date)
            circuits = circ_query.all()
            total_md += sum((c.md_kw for c in circuits), Decimal("0"))

            circuit_ids = [c.id for c in circuits]
            if circuit_ids:
                sub_query = db.query(SubCircuit).filter(
                    SubCircuit.circuit_id.in_(circuit_ids),
                    SubCircuit.status == "operative_normal",
                )
                if start_date:
                    sub_query = sub_query.filter(SubCircuit.created_at >= start_date)
                if end_date:
                    sub_query = sub_query.filter(SubCircuit.created_at <= end_date)
                sub_circuits = sub_query.all()
                total_md += sum((s.md_kw for s in sub_circuits), Decimal("0"))

        capacity = float(station.transformer_capacity_kw)
        demand = float(total_md)
        data.append({
            "station_id": station.id,
            "station_name": station.name,
            "station_code": station.code,
            "transformer_capacity_kw": capacity,
            "max_demand_kw": demand,
            "available_power_kw": capacity - demand,
            "status": station.status,
        })

    return data


@router.get("/requests-per-station")
def get_requests_per_station(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_reports")),
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
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from openpyxl import Workbook

    wb = Workbook()

    # Sheet 1: Demand evolution (current state, no date filter)
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

    # Sheet 2: Requests per station (with date filter and per-status counts)
    ws2 = wb.create_sheet("Solicitudes por Estacion")
    ws2.append(["Estacion", "Pendientes", "Aprobadas", "Rechazadas", "Total"])

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

    data: dict = {}
    for station_id, station_name, status, count in results:
        if station_name not in data:
            data[station_name] = {"pending": 0, "approved": 0, "rejected": 0}
        data[station_name][status] = count

    for name, counts in data.items():
        total = counts["pending"] + counts["approved"] + counts["rejected"]
        ws2.append([name, counts["pending"], counts["approved"], counts["rejected"], total])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = "reportes.xlsx"
    if start_date or end_date:
        s = start_date.strftime("%Y-%m-%d") if start_date else "inicio"
        e = end_date.strftime("%Y-%m-%d") if end_date else "fin"
        filename = f"reportes_{s}_{e}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
