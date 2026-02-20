from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin, check_permission
from app.models.user import User
from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.bar import Bar
from app.schemas.sub_circuit import SubCircuitCreate, SubCircuitUpdate, SubCircuitResponse, SubCircuitStatusUpdate
from app.services.energy_calculator import EnergyCalculator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/sub-circuits", tags=["Sub-Circuits"])


@router.get("/circuit/{circuit_id}", response_model=list[SubCircuitResponse])
def get_sub_circuits(
    circuit_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("view_circuits")),
):
    return (
        db.query(SubCircuit)
        .filter(SubCircuit.circuit_id == circuit_id)
        .order_by(SubCircuit.id)
        .all()
    )


@router.post("/circuit/{circuit_id}", response_model=SubCircuitResponse)
def create_sub_circuit(
    circuit_id: int,
    data: SubCircuitCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")

    md_kw = data.md_kw if data.md_kw is not None else data.pi_kw * data.fd

    sub = SubCircuit(
        circuit_id=circuit_id,
        name=data.name,
        description=data.description,
        itm=data.itm,
        mm2=data.mm2,
        pi_kw=data.pi_kw,
        fd=data.fd,
        md_kw=md_kw,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Recalculate station energy (sub-circuits affect totals)
    bar = db.query(Bar).filter(Bar.id == circuit.bar_id).first()
    if bar:
        EnergyCalculator(db).recalculate_station(bar.station_id)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CREATE_SUB_CIRCUIT",
        entity_type="sub_circuit",
        entity_id=sub.id,
        details={"name": sub.name, "circuit_id": circuit_id},
    )

    return sub


@router.delete("/{sub_circuit_id}")
def delete_sub_circuit(
    sub_circuit_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    sub = db.query(SubCircuit).filter(SubCircuit.id == sub_circuit_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Sub-circuito no encontrado")

    info = {"name": sub.name, "circuit_id": sub.circuit_id}
    circuit_id = sub.circuit_id
    db.delete(sub)
    db.commit()

    # Recalculate station energy (sub-circuits affect totals)
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if circuit:
        bar = db.query(Bar).filter(Bar.id == circuit.bar_id).first()
        if bar:
            EnergyCalculator(db).recalculate_station(bar.station_id)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="DELETE_SUB_CIRCUIT",
        entity_type="sub_circuit",
        entity_id=sub_circuit_id,
        details=info,
    )

    return {"message": "Sub-circuito eliminado exitosamente"}


@router.put("/{sub_circuit_id}/status", response_model=SubCircuitResponse)
def update_sub_circuit_status(
    sub_circuit_id: int,
    data: SubCircuitStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    sub = db.query(SubCircuit).filter(SubCircuit.id == sub_circuit_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Sub-circuito no encontrado")

    old_status = sub.status
    sub.status = data.status

    if data.status in ("reserve_r", "reserve_equipped_re") and old_status == "operative_normal":
        sub.reserve_since = date.today()
    elif data.status == "operative_normal":
        sub.reserve_since = None

    db.commit()
    db.refresh(sub)

    circuit = db.query(Circuit).filter(Circuit.id == sub.circuit_id).first()
    if circuit:
        bar = db.query(Bar).filter(Bar.id == circuit.bar_id).first()
        if bar:
            EnergyCalculator(db).recalculate_station(bar.station_id)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CHANGE_SUB_CIRCUIT_STATUS",
        entity_type="sub_circuit",
        entity_id=sub.id,
        details={"old_status": old_status, "new_status": data.status},
    )

    return sub
