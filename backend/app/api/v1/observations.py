from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, check_permission, require_admin
from app.models.user import User
from app.models.observation import Observation
from app.schemas.observation import ObservationCreate, ObservationResponse
from app.services.audit_service import AuditService

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


@router.get(
    "/circuit/{circuit_id}",
    response_model=list[ObservationResponse],
    summary="Observaciones de un circuito",
    description="Retorna las observaciones del circuito indicado, ordenadas por fecha (más recientes primero). Cualquier usuario autenticado puede verlas.",
    response_description="Lista de observaciones del circuito",
    responses={401: {"description": "No autenticado"}},
)
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


@router.get(
    "/bar/{bar_id}",
    response_model=list[ObservationResponse],
    summary="Observaciones de una barra",
    description="Retorna las observaciones de la barra indicada, ordenadas por fecha. Cualquier usuario autenticado puede verlas.",
    response_description="Lista de observaciones de la barra",
    responses={401: {"description": "No autenticado"}},
)
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


@router.post(
    "",
    response_model=ObservationResponse,
    summary="Crear observación",
    description="""Crea una observación técnica sobre un elemento de la infraestructura. **Requiere permiso:** `add_observations`\n\nDebe especificarse al menos uno de: `circuit_id`, `sub_circuit_id` o `bar_id`.\n\nSeveridades:\n- `urgent` — Requiere atención inmediata\n- `warning` — Advertencia técnica\n- `recommendation` — Sugerencia de mejora""",
    response_description="Datos de la observación creada",
    responses={400: {"description": "Severidad inválida o ningún elemento especificado"}, 401: {"description": "No autenticado"}, 403: {"description": "Permiso add_observations no habilitado"}},
)
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


@router.delete(
    "/{observation_id}",
    status_code=204,
    summary="Eliminar observación",
    description="Elimina una observación existente. Solo admin. La acción queda registrada en auditoría.",
    response_description="Sin contenido (204)",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Observación no encontrada"}},
)
def delete_observation(
    observation_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observacion no encontrada")

    obs_info = {
        "content": obs.content,
        "severity": obs.severity,
        "user_id": obs.user_id,
        "circuit_id": obs.circuit_id,
        "bar_id": obs.bar_id,
    }

    db.delete(obs)
    db.commit()

    AuditService(db).log(
        user=admin,
        action="DELETE_OBSERVATION",
        entity_type="observation",
        entity_id=observation_id,
        details=obs_info,
    )
