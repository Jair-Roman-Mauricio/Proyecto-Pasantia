from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_admin, check_permission
from app.subest_client import get_subest_client
from app.schemas.sub_circuit import SubCircuitCreate, SubCircuitUpdate, SubCircuitResponse, SubCircuitStatusUpdate
from app.services.energy_calculator import EnergyCalculator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/sub-circuits", tags=["Sub-Circuits"])


def _get_station_id(client, circuit_id: int) -> int | None:
    circuit = client.table("circuits").select("bar_id").eq("id", circuit_id).execute()
    if not circuit.data:
        return None
    bar = client.table("bars").select("station_id").eq("id", circuit.data[0]["bar_id"]).execute()
    return bar.data[0]["station_id"] if bar.data else None


@router.get("/circuit/{circuit_id}", response_model=list[SubCircuitResponse])
def get_sub_circuits(circuit_id: int, _=Depends(check_permission("view_circuits"))):
    client = get_subest_client()
    result = client.table("sub_circuits").select("*").eq("circuit_id", circuit_id).order("id").execute()
    return result.data


@router.post("/circuit/{circuit_id}", response_model=SubCircuitResponse, status_code=201)
def create_sub_circuit(circuit_id: int, data: SubCircuitCreate, admin=Depends(require_admin)):
    client = get_subest_client()
    circuit_result = client.table("circuits").select("*").eq("id", circuit_id).execute()
    if not circuit_result.data:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")

    md_kw = data.md_kw if data.md_kw is not None else data.pi_kw * data.fd
    payload = {
        "circuit_id": circuit_id,
        "name": data.name,
        "description": data.description,
        "itm": data.itm,
        "mm2": data.mm2,
        "pi_kw": float(data.pi_kw),
        "fd": float(data.fd),
        "md_kw": float(md_kw),
        "status": data.status,
    }
    if data.status in ("reserve_r", "reserve_equipped_re"):
        payload["reserve_since"] = date.today().isoformat()
        payload["reserve_expires_at"] = data.reserve_expires_at.isoformat() if data.reserve_expires_at else None

    result = client.table("sub_circuits").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear sub-circuito")
    sub = result.data[0]

    station_id = _get_station_id(client, circuit_id)
    if station_id:
        EnergyCalculator().recalculate_station(station_id)

    AuditService().log(user=admin, action="CREATE_SUB_CIRCUIT", entity_type="sub_circuit", entity_id=sub["id"],
                       details={"name": sub["name"], "circuit_id": circuit_id})
    return sub


@router.put("/{sub_circuit_id}", response_model=SubCircuitResponse)
def update_sub_circuit(sub_circuit_id: int, data: SubCircuitUpdate, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("sub_circuits").select("*").eq("id", sub_circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Sub-circuito no encontrado")
    sub = result.data[0]

    patch = {}
    for field in ("name", "description", "itm", "mm2", "pi_kw", "fd", "md_kw"):
        val = getattr(data, field, None)
        if val is not None:
            patch[field] = float(val) if isinstance(val, Decimal) else val

    if "md_kw" not in patch and ("pi_kw" in patch or "fd" in patch):
        pi = patch.get("pi_kw", sub["pi_kw"])
        fd = patch.get("fd", sub["fd"])
        patch["md_kw"] = float(Decimal(str(pi)) * Decimal(str(fd)))

    updated = client.table("sub_circuits").update(patch).eq("id", sub_circuit_id).execute()
    if not updated.data:
        raise HTTPException(status_code=500, detail="Error al actualizar sub-circuito")

    station_id = _get_station_id(client, sub["circuit_id"])
    if station_id:
        EnergyCalculator().recalculate_station(station_id)

    AuditService().log(user=admin, action="UPDATE_SUB_CIRCUIT", entity_type="sub_circuit", entity_id=sub_circuit_id,
                       details={"name": updated.data[0]["name"]})
    return updated.data[0]


@router.put("/{sub_circuit_id}/status", response_model=SubCircuitResponse)
def update_sub_circuit_status(sub_circuit_id: int, data: SubCircuitStatusUpdate, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("sub_circuits").select("*").eq("id", sub_circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Sub-circuito no encontrado")
    sub = result.data[0]
    old_status = sub["status"]

    patch = {"status": data.status}
    if data.status in ("reserve_r", "reserve_equipped_re") and old_status == "operative_normal":
        patch["reserve_since"] = date.today().isoformat()
        patch["reserve_expires_at"] = data.reserve_expires_at.isoformat() if data.reserve_expires_at else None
    elif data.status == "operative_normal":
        patch["reserve_since"] = None
        patch["reserve_expires_at"] = None

    updated = client.table("sub_circuits").update(patch).eq("id", sub_circuit_id).execute()
    if not updated.data:
        raise HTTPException(status_code=500, detail="Error al cambiar estado")

    station_id = _get_station_id(client, sub["circuit_id"])
    if station_id:
        EnergyCalculator().recalculate_station(station_id)

    AuditService().log(user=admin, action="CHANGE_SUB_CIRCUIT_STATUS", entity_type="sub_circuit", entity_id=sub_circuit_id,
                       details={"old_status": old_status, "new_status": data.status})
    return updated.data[0]


@router.delete("/{sub_circuit_id}")
def delete_sub_circuit(sub_circuit_id: int, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("sub_circuits").select("*").eq("id", sub_circuit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Sub-circuito no encontrado")
    sub = result.data[0]
    info = {"name": sub["name"], "circuit_id": sub["circuit_id"]}

    client.table("sub_circuits").delete().eq("id", sub_circuit_id).execute()

    station_id = _get_station_id(client, sub["circuit_id"])
    if station_id:
        EnergyCalculator().recalculate_station(station_id)

    AuditService().log(user=admin, action="DELETE_SUB_CIRCUIT", entity_type="sub_circuit", entity_id=sub_circuit_id,
                       details=info)
    return {"message": "Sub-circuito eliminado exitosamente"}
