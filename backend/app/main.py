from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.api.v1.router import api_router
from app.database import engine, Base, SessionLocal
from app.models import *  # noqa: F401 - Import all models for table creation

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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Intente nuevamente."},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup():
    Base.metadata.create_all(bind=engine)
    await _seed_initial_data()

    from app.services.notification_service import check_expiring_reserves

    def run_reserve_check():
        db = SessionLocal()
        try:
            check_expiring_reserves(db)
        except Exception:
            pass
        finally:
            db.close()

    run_reserve_check()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_reserve_check, "cron", hour=8, minute=0)
    scheduler.start()


async def _seed_initial_data():
    import uuid
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.user import User
    from app.models.station import Station
    from app.models.bar import Bar
    from app.utils.constants import STATIONS, BAR_TYPES
    from app.utils.supabase_admin import create_supabase_auth_user

    db: Session = SessionLocal()
    try:
        # Crear las 26 estaciones y sus 3 barras si la tabla está vacía
        count = db.query(Station).count()
        if count == 0:
            for station_data in STATIONS:
                station = Station(
                    code=station_data["code"],
                    name=station_data["name"],
                    order_index=station_data["order_index"],
                    transformer_capacity_kw=500,
                    max_demand_kw=0,
                    available_power_kw=500,
                    status="green",
                )
                db.add(station)
            db.commit()

            stations = db.query(Station).all()
            for station in stations:
                for bar_data in BAR_TYPES:
                    bar = Bar(
                        station_id=station.id,
                        name=bar_data["name"],
                        bar_type=bar_data["bar_type"],
                        status="operative",
                        capacity_kw=200,
                        capacity_a=300,
                    )
                    db.add(bar)
            db.commit()

        # Crear usuario admin por defecto si no existe ninguno en la BD
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            try:
                supabase_user = await create_supabase_auth_user(
                    email="admin@linea1metro.internal",
                    password="admin123",
                    username="admin",
                    role="admin",
                    full_name="Administrador",
                )
                admin = User(
                    id=uuid.UUID(supabase_user["id"]),
                    username="admin",
                    full_name="Administrador del Sistema",
                    role="admin",
                    status="active",
                )
                db.add(admin)
                db.commit()
                print("[SEED] Usuario admin creado correctamente.")
            except Exception as e:
                print(f"[SEED] No se pudo crear el admin en Supabase: {e}")
                print("[SEED] Crea el usuario admin manualmente en Supabase Studio.")

    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Linea 1 Metro - Sistema de Gestion Energetica API", "docs": "/docs"}
