from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_admin, check_permission
from app.subest_client import get_subest_client
from app.schemas.circuit import CircuitCreate, CircuitUpdate, CircuitStatusUpdate, CircuitResponse
from app.services.energy_calculator import EnergyCalculator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/circuits", tags=["Circuits"])


@router.get("/bar/{bar_id}", response_model=list[CircuitResponse])
def get_circuits_by_bar(bar_id: int, _=Depends(check_permission("view_circuits"))):
    client = get_subest_client()
    result = client.table("circuits").select("*").eq("bar_id", bar_id).order("id").execute()
    return result.data


@router.get("/{circuit_id}", response_model=CircuitResponse)
def get_circuit(circuit_id: int, _=Depends(check_permission("view_circuits"))):
    client = get_subest_client()
    result = client.table("circuits").select("*").eq("id", circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    return result.data[0]


@router.post("/bar/{bar_id}", response_model=CircuitResponse, status_code=201)
def create_circuit(bar_id: int, data: CircuitCreate, admin=Depends(require_admin)):
    client = get_subest_client()
    bar_result = client.table("bars").select("*").eq("id", bar_id).execute()
    if not bar_result.data:
        raise HTTPException(status_code=404, detail="Barra no encontrada")
    bar = bar_result.data[0]

    md_kw = data.md_kw if data.md_kw is not None else data.pi_kw * data.fd

    calculator = EnergyCalculator()
    if not data.force:
        check = calculator.check_capacity(bar_id, md_kw)
        if not check["can_add"]:
            raise HTTPException(status_code=400, detail={
                "message": check["message"],
                "available_before": check["available_before"],
                "available_after": check["available_after"],
                "requires_force": True,
            })

    if data.is_ups:
        if not data.secondary_bar_id or not data.tertiary_bar_id:
            raise HTTPException(status_code=400, detail="UPS requiere dos barras de conexion")
        if data.secondary_bar_id == bar_id or data.tertiary_bar_id == bar_id:
            raise HTTPException(status_code=400, detail="Las barras de conexion deben ser diferentes a la primaria")
        if data.secondary_bar_id == data.tertiary_bar_id:
            raise HTTPException(status_code=400, detail="Las dos barras de conexion deben ser diferentes entre si")

    if data.status in ("reserve_r", "reserve_equipped_re") and not data.reserve_expires_at:
        raise HTTPException(status_code=400, detail="Los circuitos en reserva requieren fecha de vencimiento")

    payload = {
        "bar_id": bar_id,
        "secondary_bar_id": data.secondary_bar_id if data.is_ups else None,
        "tertiary_bar_id": data.tertiary_bar_id if data.is_ups else None,
        "denomination": data.denomination,
        "name": data.name,
        "description": data.description,
        "local_item": data.local_item,
        "pi_kw": float(data.pi_kw),
        "fd": float(data.fd),
        "md_kw": float(md_kw),
        "status": data.status,
        "is_ups": data.is_ups,
    }
    if data.status in ("reserve_r", "reserve_equipped_re"):
        payload["reserve_since"] = date.today().isoformat()
        payload["reserve_expires_at"] = data.reserve_expires_at.isoformat() if data.reserve_expires_at else None

    result = client.table("circuits").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear circuito")
    circuit = result.data[0]

    calculator.recalculate_station(bar["station_id"])

    AuditService().log(
        user=admin,
        action="CREATE_CIRCUIT",
        entity_type="circuit",
        entity_id=circuit["id"],
        details={"name": circuit["name"], "bar_id": bar_id, "md_kw": float(md_kw)},
    )
    return circuit


@router.put("/{circuit_id}", response_model=CircuitResponse)
def update_circuit(circuit_id: int, data: CircuitUpdate, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("circuits").select("*").eq("id", circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    circuit = result.data[0]

    update_data = data.model_dump(exclude_unset=True)
    if "pi_kw" in update_data or "fd" in update_data:
        pi = update_data.get("pi_kw", circuit["pi_kw"])
        fd = update_data.get("fd", circuit["fd"])
        if "md_kw" not in update_data:
            update_data["md_kw"] = float(Decimal(str(pi)) * Decimal(str(fd)))

    # Convert Decimal/date fields to serializable types
    for k, v in update_data.items():
        if hasattr(v, 'isoformat'):
            update_data[k] = v.isoformat()
        elif isinstance(v, Decimal):
            update_data[k] = float(v)

    updated = client.table("circuits").update(update_data).eq("id", circuit_id).execute()
    if not updated.data:
        raise HTTPException(status_code=500, detail="Error al actualizar circuito")

    bar_result = client.table("bars").select("station_id").eq("id", circuit["bar_id"]).execute()
    if bar_result.data:
        EnergyCalculator().recalculate_station(bar_result.data[0]["station_id"])

    AuditService().log(user=admin, action="UPDATE_CIRCUIT", entity_type="circuit", entity_id=circuit_id,
                       details={"updated_fields": list(update_data.keys())})
    return updated.data[0]


@router.put("/{circuit_id}/status", response_model=CircuitResponse)
def update_circuit_status(circuit_id: int, data: CircuitStatusUpdate, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("circuits").select("*").eq("id", circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    circuit = result.data[0]
    old_status = circuit["status"]

    patch = {"status": data.status}
    if data.status in ("reserve_r", "reserve_equipped_re") and old_status == "operative_normal":
        patch["reserve_since"] = date.today().isoformat()
        patch["reserve_expires_at"] = data.reserve_expires_at.isoformat() if data.reserve_expires_at else None
    elif data.status == "operative_normal":
        patch["reserve_since"] = None
        patch["reserve_expires_at"] = None

    updated = client.table("circuits").update(patch).eq("id", circuit_id).execute()
    if not updated.data:
        raise HTTPException(status_code=500, detail="Error al cambiar estado")

    bar_result = client.table("bars").select("station_id").eq("id", circuit["bar_id"]).execute()
    if bar_result.data:
        EnergyCalculator().recalculate_station(bar_result.data[0]["station_id"])

    AuditService().log(user=admin, action="CHANGE_CIRCUIT_STATUS", entity_type="circuit", entity_id=circuit_id,
                       details={"old_status": old_status, "new_status": data.status})
    return updated.data[0]


@router.delete("/{circuit_id}")
def delete_circuit(circuit_id: int, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("circuits").select("*").eq("id", circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    circuit = result.data[0]

    bar_result = client.table("bars").select("station_id").eq("id", circuit["bar_id"]).execute()
    client.table("circuits").delete().eq("id", circuit_id).execute()

    if bar_result.data:
        EnergyCalculator().recalculate_station(bar_result.data[0]["station_id"])

    AuditService().log(user=admin, action="DELETE_CIRCUIT", entity_type="circuit", entity_id=circuit_id,
                       details={"name": circuit["name"], "bar_id": circuit["bar_id"]})
    return {"message": "Circuito eliminado exitosamente"}
