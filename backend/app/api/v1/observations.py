from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, check_permission
from app.models.user import User
from app.models.observation import Observation
from app.schemas.observation import ObservationCreate, ObservationResponse

router = APIRouter(prefix="/observations", tags=["Observations"])


def _enrich(obs: Observation, db: Session) -> ObservationResponse:
    user = db.query(User).filter(User.id == obs.user_id).first()
    return ObservationResponse(
        id=obs.id,
        circuit_id=obs.circuit_id,
        sub_circuit_id=obs.sub_circuit_id,
        bar_id=obs.bar_id,
        user_id=obs.user_id,
        user_name=user.full_name if user else None,
        user_role=user.role if user else None,
        severity=obs.severity,
        content=obs.content,
        created_at=obs.created_at,
    )


@router.get("/circuit/{circuit_id}", response_model=list[ObservationResponse])
def get_circuit_observations(
    circuit_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obs = (
        db.query(Observation)
        .filter(Observation.circuit_id == circuit_id)
        .order_by(Observation.created_at.desc())
        .all()
    )
    return [_enrich(o, db) for o in obs]


@router.get("/bar/{bar_id}", response_model=list[ObservationResponse])
def get_bar_observations(
    bar_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obs = (
        db.query(Observation)
        .filter(Observation.bar_id == bar_id)
        .order_by(Observation.created_at.desc())
        .all()
    )
    return [_enrich(o, db) for o in obs]


@router.post("", response_model=ObservationResponse)
def create_observation(
    data: ObservationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(check_permission("add_observations")),
):
    if data.severity not in ("urgent", "warning", "recommendation"):
        raise HTTPException(status_code=400, detail="Severidad invalida")

    if not any([data.circuit_id, data.sub_circuit_id, data.bar_id]):
        raise HTTPException(
            status_code=400,
            detail="Debe especificar circuit_id, sub_circuit_id o bar_id",
        )

    obs = Observation(
        circuit_id=data.circuit_id,
        sub_circuit_id=data.sub_circuit_id,
        bar_id=data.bar_id,
        user_id=user.id,
        severity=data.severity,
        content=data.content,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)

    return _enrich(obs, db)
