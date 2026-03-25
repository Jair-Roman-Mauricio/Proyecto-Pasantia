from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="Línea 1 Metro — API de Gestión Energética",
    description="""
## Sistema de Gestión Energética — Línea 1 del Metro de Lima

API REST para la administración de la infraestructura eléctrica de las **26 estaciones** de la Línea 1 del Metro de Lima.

### Autenticación

El login se realiza directamente con **Supabase Auth** desde el frontend.
Todos los endpoints protegidos requieren el token JWT de Supabase en el header:
```
Authorization: Bearer <supabase_access_token>
```

### Roles de usuario

| Rol | Descripción |
|-----|-------------|
| **admin** | Acceso total: gestión de circuitos, aprobación de solicitudes, auditoría, backups |
| **opersac** | Acceso limitado por permisos: puede enviar solicitudes, ver estaciones y reportes |

### Jerarquía de datos
```
Estación → Barra (normal / emergencia / continuidad) → Circuito → Sub-circuito
```
    """,
    version="1.2.0",
    contact={"name": "Administración del Sistema", "email": "admin@linea1metro.pe"},
    license_info={"name": "Uso interno — Línea 1 Metro de Lima"},
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    openapi_tags=[
        {"name": "Auth", "description": "Verificación de sesión Supabase. El login ocurre en el frontend con supabase-js."},
        {"name": "Users", "description": "Gestión de usuarios del sistema. Solo accesible por administradores."},
        {"name": "Stations", "description": "Estaciones de la Línea 1 (E01 Villa El Salvador → E26 Bayóvar)."},
        {"name": "Bars", "description": "Barras eléctricas de cada estación: normal, emergencia y continuidad."},
        {"name": "Circuits", "description": "Circuitos eléctricos instalados en cada barra."},
        {"name": "Sub-Circuits", "description": "Sub-circuitos (ampliaciones) dentro de un circuito existente."},
        {"name": "Requests", "description": "Solicitudes de ampliación de carga enviadas por operadores OPERSAC."},
        {"name": "Observations", "description": "Notas y observaciones técnicas sobre circuitos, sub-circuitos o barras."},
        {"name": "Notifications", "description": "Alertas automáticas del sistema sobre reservas próximas a vencer. Solo admin."},
        {"name": "Permissions", "description": "Control de acceso por feature para usuarios OPERSAC."},
        {"name": "Audit", "description": "Log de todas las acciones realizadas en el sistema. Solo admin."},
        {"name": "Backups", "description": "Respaldos completos de la base de datos en formato JSON. Solo admin."},
        {"name": "Reports", "description": "Reportes de demanda eléctrica y solicitudes por estación."},
        {"name": "Images", "description": "Imágenes asociadas a estaciones, barras o circuitos."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[VALIDATION ERROR] {request.method} {request.url}: {exc}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, RequestValidationError)):
        raise exc
    import traceback
    print(f"[ERROR 500] {request.method} {request.url}: {type(exc).__name__}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {str(exc)}"},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup():
    _seed_initial_data()

    from app.services.notification_service import check_expiring_reserves

    def run_reserve_check():
        try:
            check_expiring_reserves()
        except Exception as e:
            print(f"[RESERVE CHECK] Error: {e}")

    run_reserve_check()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_reserve_check, "cron", hour=8, minute=0)
    scheduler.start()


def _seed_initial_data():
    from app.subest_client import get_subest_client
    from app.utils.constants import STATIONS, BAR_TYPES

    try:
        client = get_subest_client()

        # Crear las 26 estaciones si la tabla está vacía
        count_result = client.table("stations").select("id", count="exact").execute()
        count = count_result.count if hasattr(count_result, 'count') and count_result.count is not None else len(count_result.data)

        if count == 0:
            for s in STATIONS:
                result = client.table("stations").insert({
                    "code": s["code"],
                    "name": s["name"],
                    "order_index": s["order_index"],
                    "transformer_capacity_kw": 500,
                    "max_demand_kw": 0,
                    "available_power_kw": 500,
                    "status": "green",
                }).execute()
                if result.data:
                    station_id = result.data[0]["id"]
                    for bar_data in BAR_TYPES:
                        client.table("bars").insert({
                            "station_id": station_id,
                            "name": bar_data["name"],
                            "bar_type": bar_data["bar_type"],
                            "status": "operative",
                            "capacity_kw": 200,
                            "capacity_a": 300,
                        }).execute()
            print("[SEED] 26 estaciones y barras creadas en Supabase.")
        else:
            print(f"[SEED] Supabase ya tiene {count} estaciones. Skip.")
    except Exception as e:
        print(f"[SEED] Error al inicializar datos en Supabase: {e}")


@app.get("/")
def root():
    return {"message": "Linea 1 Metro - Sistema de Gestion Energetica API", "docs": "/docs"}


@app.get("/version")
def version():
    return {"version": "v2-debug"}
