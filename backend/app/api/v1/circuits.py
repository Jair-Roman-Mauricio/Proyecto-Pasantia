from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.schemas.circuit import CircuitCreate, CircuitUpdate, CircuitStatusUpdate, CircuitResponse
from app.services.energy_calculator import EnergyCalculator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/circuits", tags=["Circuits"])


@router.get("/bar/{bar_id}", response_model=list[CircuitResponse])
def get_circuits_by_bar(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    circuits = (
        db.query(Circuit)
        .filter(Circuit.bar_id == bar_id)
        .order_by(Circuit.id)
        .all()
    )
    return circuits


@router.get("/{circuit_id}", response_model=CircuitResponse)
def get_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    return circuit


@router.post("/bar/{bar_id}", response_model=CircuitResponse)
def create_circuit(
    bar_id: int,
    data: CircuitCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    bar = db.query(Bar).filter(Bar.id == bar_id).first()
    if not bar:
        raise HTTPException(status_code=404, detail="Barra no encontrada")

    # Auto-calculate MD if not provided
    md_kw = data.md_kw if data.md_kw is not None else data.pi_kw * data.fd

    # Check capacity
    calculator = EnergyCalculator(db)
    if not data.force:
        check = calculator.check_capacity(bar_id, md_kw)
        if not check["can_add"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": check["message"],
                    "available_before": check["available_before"],
                    "available_after": check["available_after"],
                    "requires_force": True,
                },
            )

    # Validate UPS
    if data.is_ups and not data.secondary_bar_id:
        raise HTTPException(
            status_code=400,
            detail="UPS requiere una barra secundaria (secondary_bar_id)",
        )
    if data.is_ups and data.secondary_bar_id == bar_id:
        raise HTTPException(
            status_code=400,
            detail="La barra secundaria debe ser diferente a la primaria",
        )

    circuit = Circuit(
        bar_id=bar_id,
        secondary_bar_id=data.secondary_bar_id if data.is_ups else None,
        denomination=data.denomination,
        name=data.name,
        description=data.description,
        local_item=data.local_item,
        pi_kw=data.pi_kw,
        fd=data.fd,
        md_kw=md_kw,
        status=data.status,
        is_ups=data.is_ups,
    )

    if data.status in ("reserve_r", "reserve_equipped_re"):
        circuit.reserve_since = date.today()

    db.add(circuit)
    db.commit()
    db.refresh(circuit)

    # Recalculate station energy
    calculator.recalculate_station(bar.station_id)

    # Audit
    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CREATE_CIRCUIT",
        entity_type="circuit",
        entity_id=circuit.id,
        details={
            "name": circuit.name,
            "denomination": circuit.denomination,
            "bar_id": bar_id,
            "pi_kw": float(circuit.pi_kw),
            "md_kw": float(circuit.md_kw),
            "is_ups": circuit.is_ups,
        },
    )

    return circuit


@router.put("/{circuit_id}", response_model=CircuitResponse)
def update_circuit(
    circuit_id: int,
    data: CircuitUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Recalculate MD if PI or FD changed
    if "pi_kw" in update_data or "fd" in update_data:
        pi = update_data.get("pi_kw", circuit.pi_kw)
        fd = update_data.get("fd", circuit.fd)
        if "md_kw" not in update_data:
            update_data["md_kw"] = pi * fd

    for field, value in update_data.items():
        setattr(circuit, field, value)

    db.commit()
    db.refresh(circuit)

    # Recalculate station energy
    bar = db.query(Bar).filter(Bar.id == circuit.bar_id).first()
    calculator = EnergyCalculator(db)
    calculator.recalculate_station(bar.station_id)

    # Audit
    audit = AuditService(db)
    audit.log(
        user=admin,
        action="UPDATE_CIRCUIT",
        entity_type="circuit",
        entity_id=circuit.id,
        details={"updated_fields": list(update_data.keys())},
    )

    return circuit


@router.put("/{circuit_id}/status", response_model=CircuitResponse)
def update_circuit_status(
    circuit_id: int,
    data: CircuitStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")

    old_status = circuit.status
    circuit.status = data.status

    if data.status in ("reserve_r", "reserve_equipped_re") and old_status == "operative_normal":
        circuit.reserve_since = date.today()
    elif data.status == "operative_normal":
        circuit.reserve_since = None

    db.commit()
    db.refresh(circuit)

    bar = db.query(Bar).filter(Bar.id == circuit.bar_id).first()
    calculator = EnergyCalculator(db)
    calculator.recalculate_station(bar.station_id)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CHANGE_CIRCUIT_STATUS",
        entity_type="circuit",
        entity_id=circuit.id,
        details={"old_status": old_status, "new_status": data.status},
    )

    return circuit


@router.delete("/{circuit_id}")
def delete_circuit(
    circuit_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")

    bar = db.query(Bar).filter(Bar.id == circuit.bar_id).first()
    circuit_info = {
        "name": circuit.name,
        "denomination": circuit.denomination,
        "bar_id": circuit.bar_id,
    }

    db.delete(circuit)
    db.commit()

    calculator = EnergyCalculator(db)
    calculator.recalculate_station(bar.station_id)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="DELETE_CIRCUIT",
        entity_type="circuit",
        entity_id=circuit_id,
        details=circuit_info,
    )

    return {"message": "Circuito eliminado exitosamente"}
