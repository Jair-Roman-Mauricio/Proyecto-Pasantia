from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, check_permission, require_admin
from app.subest_client import get_subest_client
from app.schemas.observation import ObservationCreate, ObservationResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/observations", tags=["Observations"])


def _enrich(obs: dict, client) -> dict:
    user = client.table("users").select("full_name,role").eq("id", str(obs["user_id"])).execute()
    return {
        **obs,
        "user_name": user.data[0]["full_name"] if user.data else None,
        "user_role": user.data[0]["role"] if user.data else None,
    }


@router.get("/circuit/{circuit_id}", response_model=list[ObservationResponse])
def get_circuit_observations(circuit_id: int, _=Depends(get_current_user)):
    client = get_subest_client()
    result = client.table("observations").select("*").eq("circuit_id", circuit_id).order("created_at", desc=True).execute()
    return [_enrich(o, client) for o in result.data]


@router.get("/bar/{bar_id}", response_model=list[ObservationResponse])
def get_bar_observations(bar_id: int, _=Depends(get_current_user)):
    client = get_subest_client()
    result = client.table("observations").select("*").eq("bar_id", bar_id).order("created_at", desc=True).execute()
    return [_enrich(o, client) for o in result.data]


@router.post("", response_model=ObservationResponse)
def create_observation(data: ObservationCreate, user=Depends(check_permission("add_observations"))):
    if data.severity not in ("urgent", "warning", "recommendation"):
        raise HTTPException(status_code=400, detail="Severidad invalida")
    if not any([data.circuit_id, data.sub_circuit_id, data.bar_id]):
        raise HTTPException(status_code=400, detail="Debe especificar circuit_id, sub_circuit_id o bar_id")

    client = get_subest_client()
    result = client.table("observations").insert({
        "circuit_id": data.circuit_id,
        "sub_circuit_id": data.sub_circuit_id,
        "bar_id": data.bar_id,
        "user_id": str(user.id),
        "severity": data.severity,
        "content": data.content,
    }).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear observacion")
    return _enrich(result.data[0], client)


@router.delete("/{observation_id}", status_code=204)
def delete_observation(observation_id: int, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("observations").select("*").eq("id", observation_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Observacion no encontrada")
    obs = result.data[0]
    client.table("observations").delete().eq("id", observation_id).execute()
    AuditService().log(user=admin, action="DELETE_OBSERVATION", entity_type="observation", entity_id=observation_id,
                       details={"content": obs["content"], "severity": obs["severity"]})
