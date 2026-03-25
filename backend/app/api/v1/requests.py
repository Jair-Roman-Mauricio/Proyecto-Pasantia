from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, require_admin, check_permission
from app.subest_client import get_subest_client
from app.schemas.request import RequestCreate, RequestReject, RequestResponse
from app.services.energy_calculator import EnergyCalculator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/requests", tags=["Requests"])


def _enrich(req: dict, client) -> dict:
    opersac = client.table("users").select("full_name").eq("id", str(req["opersac_user_id"])).execute()
    station = client.table("stations").select("name").eq("id", req["station_id"]).execute()
    circuit = client.table("circuits").select("name").eq("id", req["circuit_id"]).execute() if req.get("circuit_id") else None
    return {
        **req,
        "opersac_name": opersac.data[0]["full_name"] if opersac.data else None,
        "station_name": station.data[0]["name"] if station.data else None,
        "circuit_name": circuit.data[0]["name"] if circuit and circuit.data else None,
    }


@router.get("/circuit-options/{bar_id}")
def get_circuit_options_for_request(bar_id: int, _=Depends(check_permission("send_requests"))):
    client = get_subest_client()
    result = client.table("circuits").select("id,denomination,name").eq("bar_id", bar_id).order("denomination").execute()
    return result.data


@router.get("", response_model=list[RequestResponse])
def get_requests(_=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("requests").select("*").order("created_at", desc=True).execute()
    return [_enrich(r, client) for r in result.data]


@router.get("/my", response_model=list[RequestResponse])
def get_my_requests(user=Depends(check_permission("send_requests"))):
    client = get_subest_client()
    result = client.table("requests").select("*").eq("opersac_user_id", str(user.id)).order("created_at", desc=True).execute()
    return [_enrich(r, client) for r in result.data]


@router.post("", response_model=RequestResponse)
def create_request(data: RequestCreate, user=Depends(check_permission("send_requests"))):
    client = get_subest_client()
    station = client.table("stations").select("id").eq("id", data.station_id).execute()
    if not station.data:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")

    if data.bar_type not in ("normal", "emergency", "continuity"):
        raise HTTPException(status_code=400, detail="Tipo de barra invalido")

    payload = {
        "opersac_user_id": str(user.id),
        "station_id": data.station_id,
        "bar_type": data.bar_type,
        "circuit_id": data.circuit_id,
        "local_item": data.local_item,
        "requested_load_kw": float(data.requested_load_kw),
        "fd": float(data.fd),
        "sub_circuit_name": data.sub_circuit_name,
        "sub_circuit_description": data.sub_circuit_description,
        "sub_circuit_itm": data.sub_circuit_itm,
        "sub_circuit_mm2": data.sub_circuit_mm2,
        "justification": data.justification,
        "status": "pending",
    }
    result = client.table("requests").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear solicitud")
    req = result.data[0]

    AuditService().log(user=user, action="CREATE_REQUEST", entity_type="request", entity_id=req["id"],
                       details={"station_id": data.station_id, "bar_type": data.bar_type})
    return _enrich(req, client)


@router.put("/{request_id}/approve", response_model=RequestResponse)
def approve_request(request_id: int, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("requests").select("*").eq("id", request_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    req = result.data[0]

    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar solicitudes pendientes")

    bar_result = client.table("bars").select("*").eq("station_id", req["station_id"]).eq("bar_type", req["bar_type"]).execute()
    if not bar_result.data:
        raise HTTPException(status_code=404, detail="Barra no encontrada para la estacion")
    bar = bar_result.data[0]

    md_kw = float(req["requested_load_kw"]) * float(req["fd"])

    if req.get("circuit_id"):
        client.table("sub_circuits").insert({
            "circuit_id": req["circuit_id"],
            "name": req.get("sub_circuit_name") or f"Ampliacion Solicitud #{req['id']}",
            "description": req.get("sub_circuit_description") or req.get("justification"),
            "itm": req.get("sub_circuit_itm"),
            "mm2": req.get("sub_circuit_mm2"),
            "pi_kw": float(req["requested_load_kw"]),
            "fd": float(req["fd"]),
            "md_kw": md_kw,
        }).execute()
        created_entity = {"sub_circuit_created": True}
    else:
        client.table("circuits").insert({
            "bar_id": bar["id"],
            "denomination": f"AMP-{req['id']}",
            "name": f"Ampliacion Solicitud #{req['id']}",
            "description": req.get("justification"),
            "local_item": req.get("local_item"),
            "pi_kw": float(req["requested_load_kw"]),
            "fd": float(req["fd"]),
            "md_kw": md_kw,
            "status": "operative_normal",
        }).execute()
        created_entity = {"circuit_created": True}

    updated = client.table("requests").update({
        "status": "approved",
        "reviewed_by": str(admin.id),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", request_id).execute()

    EnergyCalculator().recalculate_station(req["station_id"])

    AuditService().log(user=admin, action="APPROVE_REQUEST", entity_type="request", entity_id=request_id,
                       details={**created_entity, "station_id": req["station_id"]})
    return _enrich(updated.data[0], client)


@router.put("/{request_id}/reject", response_model=RequestResponse)
def reject_request(request_id: int, data: RequestReject, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("requests").select("*").eq("id", request_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    req = result.data[0]

    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden rechazar solicitudes pendientes")

    updated = client.table("requests").update({
        "status": "rejected",
        "rejection_reason": data.rejection_reason,
        "reviewed_by": str(admin.id),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", request_id).execute()

    AuditService().log(user=admin, action="REJECT_REQUEST", entity_type="request", entity_id=request_id,
                       details={"reason": data.rejection_reason})
    return _enrich(updated.data[0], client)
