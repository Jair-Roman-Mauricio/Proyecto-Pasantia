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

### Roles de usuario

| Rol | Descripción |
|-----|-------------|
| **admin** | Acceso total: gestión de circuitos, aprobación de solicitudes, auditoría, backups |
| **opersac** | Acceso limitado por permisos: puede enviar solicitudes, ver estaciones y reportes |

### Autenticación

Todos los endpoints (excepto `/auth/login`) requieren un token JWT en el header:
```
Authorization: Bearer <token>
```

Obtén el token en `POST /api/v1/auth/login`.

### Permisos disponibles (opersac)

- `view_stations` — Ver estaciones, barras y circuitos
- `view_circuits` — Ver detalles de circuitos y sub-circuitos
- `send_requests` — Enviar solicitudes de ampliación de carga
- `add_observations` — Agregar observaciones a la infraestructura
- `view_reports` — Acceder a reportes y exportación Excel

### Jerarquía de datos
```
Estación → Barra (normal / emergencia / continuidad) → Circuito → Sub-circuito
```
    """,
    version="1.1.6",
    contact={"name": "Administración del Sistema", "email": "admin@linea1metro.pe"},
    license_info={"name": "Uso interno — Línea 1 Metro de Lima"},
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    openapi_tags=[
        {"name": "Auth", "description": "Autenticación con JWT. Obtén tu token aquí antes de usar cualquier otro endpoint."},
        {"name": "Users", "description": "Gestión de usuarios del sistema. Solo accesible por administradores."},
        {"name": "Stations", "description": "Estaciones de la Línea 1 (E01 Villa El Salvador → E26 Bayóvar). Requiere permiso `view_stations`."},
        {"name": "Bars", "description": "Barras eléctricas de cada estación: normal, emergencia y continuidad. Requiere permiso `view_stations`."},
        {"name": "Circuits", "description": "Circuitos eléctricos instalados en cada barra. Requiere permiso `view_circuits` para lectura, rol admin para escritura."},
        {"name": "Sub-Circuits", "description": "Sub-circuitos (ampliaciones) dentro de un circuito existente. Solo admin puede crear/eliminar."},
        {"name": "Requests", "description": "Solicitudes de ampliación de carga enviadas por operadores OPERSAC. Admin las aprueba o rechaza."},
        {"name": "Observations", "description": "Notas y observaciones técnicas sobre circuitos, sub-circuitos o barras. Severidades: urgent, warning, recommendation."},
        {"name": "Notifications", "description": "Alertas automáticas del sistema sobre reservas próximas a vencer sin contacto registrado. Solo admin."},
        {"name": "Permissions", "description": "Control de acceso por feature para usuarios OPERSAC. Admin gestiona los permisos de cada usuario."},
        {"name": "Audit", "description": "Log de todas las acciones realizadas en el sistema. Solo admin. Exportable a Excel."},
        {"name": "Backups", "description": "Respaldos completos de la base de datos en formato JSON. Solo admin puede crear, restaurar o eliminar."},
        {"name": "Reports", "description": "Reportes de demanda eléctrica y solicitudes por estación. Exportable a Excel con gráficos."},
        {"name": "Images", "description": "Imágenes asociadas a estaciones, barras o circuitos (unifilares, fotos). Admin sube, todos ven."},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler global — captura cualquier excepcion no manejada y devuelve 500
# en lugar de dejar caer el servidor
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Intente nuevamente."},
    )

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup():
    # Create tables if they don't exist (for development)
    Base.metadata.create_all(bind=engine)
    _seed_initial_data()

    from app.services.notification_service import check_expiring_reserves

    def run_reserve_check():
        db = SessionLocal()
        try:
            check_expiring_reserves(db)
        except Exception:
            # Si falla, el scheduler no se desregistra y reintentara manana
            pass
        finally:
            db.close()

    # Ejecutar verificación inmediata al iniciar
    run_reserve_check()

    # Programar verificación diaria a las 08:00
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_reserve_check, "cron", hour=8, minute=0)
    scheduler.start()


def _seed_initial_data():
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.user import User
    from app.models.station import Station
    from app.models.bar import Bar
    from app.utils.security import hash_password
    from app.utils.constants import STATIONS, BAR_TYPES

    db: Session = SessionLocal()
    try:
        # Seed admin user if none exists
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="Administrador del Sistema",
                role="admin",
                status="active",
            )
            db.add(admin)
            db.commit()

        # Seed stations if none exist
        count = db.query(Station).count()
        if count == 0:
            for station_data in STATIONS:
                station = Station(
                    code=station_data["code"],
                    name=station_data["name"],
                    order_index=station_data["order_index"],
                    transformer_capacity_kw=500,  # Default capacity
                    max_demand_kw=0,
                    available_power_kw=500,
                    status="green",
                )
                db.add(station)
            db.commit()

            # Seed 3 bars per station
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

    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Linea 1 Metro - Sistema de Gestion Energetica API", "docs": "/docs"}
