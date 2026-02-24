from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.api.v1.router import api_router
from app.database import engine, Base, SessionLocal
from app.models import *  # noqa: F401 - Import all models for table creation

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
