from fastapi import APIRouter, HTTPException

from app.subest_client import get_subest_client

router = APIRouter(prefix="/subest", tags=["Subest"])


@router.get("/health")
def subest_health():
    """Verifica que la conexión al schema Subest funciona correctamente."""
    try:
        client = get_subest_client()
        # Consulta liviana: trae máximo 1 fila de stations para probar conectividad
        result = client.table("stations").select("id").limit(1).execute()
        return {
            "status": "ok",
            "schema": "Subest",
            "message": "Conexión exitosa al servidor externo",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Sin conexión a Subest: {str(e)}")


# ── stations ────────────────────────────────────────────────────────────────

@router.get("/stations")
def list_stations():
    client = get_subest_client()
    result = client.table("stations").select("*").order("order_index").execute()
    return result.data


@router.post("/stations")
def create_station(data: dict):
    client = get_subest_client()
    result = client.table("stations").insert(data).execute()
    return result.data


# ── circuits ─────────────────────────────────────────────────────────────────

@router.get("/circuits")
def list_circuits():
    client = get_subest_client()
    result = client.table("circuits").select("*").execute()
    return result.data


@router.post("/circuits")
def create_circuit(data: dict):
    client = get_subest_client()
    result = client.table("circuits").insert(data).execute()
    return result.data


# ── users ────────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users():
    client = get_subest_client()
    result = client.table("users").select("*").execute()
    return result.data
