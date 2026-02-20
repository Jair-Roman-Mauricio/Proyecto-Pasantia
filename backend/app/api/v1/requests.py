from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin, check_permission
from app.models.user import User
from app.models.station import Station
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.request import Request
from app.models.sub_circuit import SubCircuit
from app.schemas.request import RequestCreate, RequestReject, RequestResponse
from app.services.energy_calculator import EnergyCalculator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/requests", tags=["Requests"])


def _enrich_request(req: Request, db: Session) -> RequestResponse:
    opersac = db.query(User).filter(User.id == req.opersac_user_id).first()
    station = db.query(Station).filter(Station.id == req.station_id).first()
    circuit = db.query(Circuit).filter(Circuit.id == req.circuit_id).first() if req.circuit_id else None
    return RequestResponse(
        id=req.id,
        opersac_user_id=req.opersac_user_id,
        opersac_name=opersac.full_name if opersac else None,
        station_id=req.station_id,
        station_name=station.name if station else None,
        bar_type=req.bar_type,
        circuit_id=req.circuit_id,
        circuit_name=circuit.name if circuit else None,
        local_item=req.local_item,
        requested_load_kw=req.requested_load_kw,
        fd=req.fd,
        sub_circuit_name=req.sub_circuit_name,
        sub_circuit_description=req.sub_circuit_description,
        sub_circuit_itm=req.sub_circuit_itm,
        sub_circuit_mm2=req.sub_circuit_mm2,
        justification=req.justification,
        status=req.status,
        rejection_reason=req.rejection_reason,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.get("/circuit-options/{bar_id}")
def get_circuit_options_for_request(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("send_requests")),
):
    circuits = (
        db.query(Circuit.id, Circuit.denomination, Circuit.name)
        .filter(Circuit.bar_id == bar_id)
        .order_by(Circuit.denomination)
        .all()
    )
    return [{"id": c.id, "denomination": c.denomination, "name": c.name} for c in circuits]


@router.get("", response_model=list[RequestResponse])
def get_requests(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    requests = db.query(Request).order_by(Request.created_at.desc()).all()
    return [_enrich_request(r, db) for r in requests]


@router.get("/my", response_model=list[RequestResponse])
def get_my_requests(
    db: Session = Depends(get_db),
    user: User = Depends(check_permission("send_requests")),
):
    requests = (
        db.query(Request)
        .filter(Request.opersac_user_id == user.id)
        .order_by(Request.created_at.desc())
        .all()
    )
    return [_enrich_request(r, db) for r in requests]


@router.post("", response_model=RequestResponse)
def create_request(
    data: RequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(check_permission("send_requests")),
):
    station = db.query(Station).filter(Station.id == data.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")

    if data.bar_type not in ("normal", "emergency", "continuity"):
        raise HTTPException(status_code=400, detail="Tipo de barra invalido")

    req = Request(
        opersac_user_id=user.id,
        station_id=data.station_id,
        bar_type=data.bar_type,
        circuit_id=data.circuit_id,
        local_item=data.local_item,
        requested_load_kw=data.requested_load_kw,
        fd=data.fd,
        sub_circuit_name=data.sub_circuit_name,
        sub_circuit_description=data.sub_circuit_description,
        sub_circuit_itm=data.sub_circuit_itm,
        sub_circuit_mm2=data.sub_circuit_mm2,
        justification=data.justification,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    audit = AuditService(db)
    audit.log(
        user=user,
        action="CREATE_REQUEST",
        entity_type="request",
        entity_id=req.id,
        details={"station_id": data.station_id, "bar_type": data.bar_type},
    )

    return _enrich_request(req, db)


@router.put("/{request_id}/approve", response_model=RequestResponse)
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar solicitudes pendientes")

    # Find the correct bar
    bar = (
        db.query(Bar)
        .filter(Bar.station_id == req.station_id, Bar.bar_type == req.bar_type)
        .first()
    )
    if not bar:
        raise HTTPException(status_code=404, detail="Barra no encontrada para la estacion")

    md_kw = req.requested_load_kw * req.fd

    if req.circuit_id:
        # Create sub-circuit on existing circuit
        sub = SubCircuit(
            circuit_id=req.circuit_id,
            name=req.sub_circuit_name or f"Ampliacion Solicitud #{req.id}",
            description=req.sub_circuit_description or req.justification,
            itm=req.sub_circuit_itm,
            mm2=req.sub_circuit_mm2,
            pi_kw=req.requested_load_kw,
            fd=req.fd,
            md_kw=md_kw,
        )
        db.add(sub)
        created_entity = {"sub_circuit_created": True}
    else:
        # Create new circuit on bar
        circuit = Circuit(
            bar_id=bar.id,
            denomination=f"AMP-{req.id}",
            name=f"Ampliacion Solicitud #{req.id}",
            description=req.justification,
            local_item=req.local_item,
            pi_kw=req.requested_load_kw,
            fd=req.fd,
            md_kw=md_kw,
            status="operative_normal",
        )
        db.add(circuit)
        created_entity = {"circuit_created": True}

    req.status = "approved"
    req.reviewed_by = admin.id
    req.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(req)

    # Recalculate energy
    calculator = EnergyCalculator(db)
    calculator.recalculate_station(req.station_id)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="APPROVE_REQUEST",
        entity_type="request",
        entity_id=req.id,
        details={**created_entity, "station_id": req.station_id},
    )

    return _enrich_request(req, db)


@router.put("/{request_id}/reject", response_model=RequestResponse)
def reject_request(
    request_id: int,
    data: RequestReject,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden rechazar solicitudes pendientes")

    req.status = "rejected"
    req.rejection_reason = data.rejection_reason
    req.reviewed_by = admin.id
    req.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(req)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="REJECT_REQUEST",
        entity_type="request",
        entity_id=req.id,
        details={"reason": data.rejection_reason},
    )

    return _enrich_request(req, db)
