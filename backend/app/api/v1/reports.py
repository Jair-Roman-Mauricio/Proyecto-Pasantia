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


@router.get(
    "/demand-evolution",
    summary="Reporte de evolución de demanda",
    description="""Retorna datos de demanda eléctrica por estación. **Requiere permiso:** `view_reports`\n\n**Sin filtros de fecha:** Retorna los valores actuales de todas las estaciones.\n\n**Con `start_date` / `end_date`:** Calcula la demanda acumulada solo de circuitos y sub-circuitos creados en ese rango de fechas.\n\nÚtil para analizar el crecimiento de carga en el tiempo.""",
    response_description="Lista de estaciones con capacidad, demanda máxima y disponible",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Permiso view_reports no habilitado"}},
)
def get_demand_evolution(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_reports")),
):
    stations = db.query(Station).order_by(Station.order_index).all()

    if not start_date and not end_date:
        # Sin filtro de fecha: retornar los valores actuales almacenados en cada estación
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

    # Con filtro de fecha: calcular la demanda acumulada de circuitos y sub-circuitos
    # creados dentro del rango indicado, para analizar el crecimiento de carga
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


@router.get(
    "/requests-per-station",
    summary="Reporte de solicitudes por estación",
    description="Retorna la cantidad de solicitudes agrupadas por estación y estado (pending, approved, rejected). Filtrable por rango de fechas. **Requiere permiso:** `view_reports`",
    response_description="Lista con conteos de solicitudes por estación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Permiso view_reports no habilitado"}},
)
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


@router.get(
    "/export/excel",
    summary="Exportar reportes a Excel",
    description="""Descarga un archivo Excel con dos hojas y gráficos incluidos. **Requiere permiso:** `view_reports`\n\n**Hoja 1 — Demanda Eléctrica:** Tabla con capacidad, demanda y disponible por estación + gráfico de líneas.\n\n**Hoja 2 — Solicitudes por Estación:** Tabla con conteos de solicitudes + gráfico de barras apiladas.\n\nFiltrable por rango de fechas (`start_date`, `end_date`).""",
    response_description="Archivo Excel (reportes.xlsx)",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Permiso view_reports no habilitado"}},
)
def export_reports_excel(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_reports")),
):
    from openpyxl import Workbook
    from openpyxl.chart import LineChart as XlLineChart, BarChart as XlBarChart, Reference
    from openpyxl.chart.series import DataPoint
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    # ── Hoja 1: Demanda Eléctrica — tabla con capacidad, demanda y disponible por estación ──
    ws1 = wb.active
    ws1.title = "Demanda Electrica"
    ws1.append(["Estacion", "Codigo", "Capacidad (kW)", "Demanda Max (kW)", "Disponible (kW)"])

    stations = db.query(Station).order_by(Station.order_index).all()

    if not start_date and not end_date:
        for s in stations:
            ws1.append([
                s.name, s.code,
                float(s.transformer_capacity_kw),
                float(s.max_demand_kw),
                float(s.available_power_kw),
            ])
    else:
        for s in stations:
            bar_ids = [b.id for b in db.query(Bar.id).filter(Bar.station_id == s.id).all()]
            total_md = Decimal("0")
            if bar_ids:
                circ_query = db.query(Circuit).filter(
                    Circuit.bar_id.in_(bar_ids), Circuit.status != "inactive",
                )
                if start_date:
                    circ_query = circ_query.filter(Circuit.created_at >= start_date)
                if end_date:
                    circ_query = circ_query.filter(Circuit.created_at <= end_date)
                circuits = circ_query.all()
                total_md += sum((c.md_kw for c in circuits), Decimal("0"))
                circuit_ids = [c.id for c in circuits]
                if circuit_ids:
                    sub_q = db.query(SubCircuit).filter(
                        SubCircuit.circuit_id.in_(circuit_ids),
                        SubCircuit.status == "operative_normal",
                    )
                    if start_date:
                        sub_q = sub_q.filter(SubCircuit.created_at >= start_date)
                    if end_date:
                        sub_q = sub_q.filter(SubCircuit.created_at <= end_date)
                    total_md += sum((sc.md_kw for sc in sub_q.all()), Decimal("0"))
            capacity = float(s.transformer_capacity_kw)
            demand = float(total_md)
            ws1.append([s.name, s.code, capacity, demand, capacity - demand])

    # Ajustar ancho de columnas para mejorar la legibilidad del Excel
    for col in range(1, 6):
        ws1.column_dimensions[get_column_letter(col)].width = 22

    num_stations = len(stations)

    # Gráfico de líneas: demanda actual vs capacidad instalada por estación
    if num_stations > 0:
        chart1 = XlLineChart()
        chart1.title = "Evolucion de Demanda Electrica"
        chart1.y_axis.title = "kW"
        chart1.x_axis.title = "Estacion"
        chart1.style = 10
        chart1.width = 28
        chart1.height = 14

        cats = Reference(ws1, min_col=1, min_row=2, max_row=1 + num_stations)
        demand_data = Reference(ws1, min_col=4, min_row=1, max_row=1 + num_stations)
        capacity_data = Reference(ws1, min_col=3, min_row=1, max_row=1 + num_stations)

        chart1.add_data(demand_data, titles_from_data=True)
        chart1.add_data(capacity_data, titles_from_data=True)
        chart1.set_categories(cats)

        # Estilo de series: demanda en rojo sólido, capacidad en verde discontinuo
        s1 = chart1.series[0]
        s1.graphicalProperties.line.solidFill = "EF4444"
        s2 = chart1.series[1]
        s2.graphicalProperties.line.solidFill = "22C55E"
        s2.graphicalProperties.line.dashStyle = "dash"

        ws1.add_chart(chart1, f"A{num_stations + 4}")

    # ── Hoja 2: Solicitudes por Estación — tabla con conteos agrupados por estado ──
    ws2 = wb.create_sheet("Solicitudes por Estacion")
    ws2.append(["Estacion", "Pendientes", "Aprobadas", "Rechazadas", "Total"])

    query = db.query(
        Request.station_id, Station.name, Request.status,
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

    for col in range(1, 6):
        ws2.column_dimensions[get_column_letter(col)].width = 20

    num_req_rows = len(data)

    # Gráfico de barras apiladas: solicitudes pendientes, aprobadas y rechazadas por estación
    if num_req_rows > 0:
        chart2 = XlBarChart()
        chart2.type = "col"
        chart2.title = "Solicitudes de Opersac por Estacion"
        chart2.y_axis.title = "Cantidad"
        chart2.x_axis.title = "Estacion"
        chart2.style = 10
        chart2.width = 28
        chart2.height = 14

        cats2 = Reference(ws2, min_col=1, min_row=2, max_row=1 + num_req_rows)
        pending_ref = Reference(ws2, min_col=2, min_row=1, max_row=1 + num_req_rows)
        approved_ref = Reference(ws2, min_col=3, min_row=1, max_row=1 + num_req_rows)
        rejected_ref = Reference(ws2, min_col=4, min_row=1, max_row=1 + num_req_rows)

        chart2.add_data(pending_ref, titles_from_data=True)
        chart2.add_data(approved_ref, titles_from_data=True)
        chart2.add_data(rejected_ref, titles_from_data=True)
        chart2.set_categories(cats2)

        # Colores de series: pendientes en amarillo, aprobadas en verde, rechazadas en rojo
        chart2.series[0].graphicalProperties.solidFill = "EAB308"
        chart2.series[1].graphicalProperties.solidFill = "22C55E"
        chart2.series[2].graphicalProperties.solidFill = "EF4444"

        ws2.add_chart(chart2, f"A{num_req_rows + 4}")

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
