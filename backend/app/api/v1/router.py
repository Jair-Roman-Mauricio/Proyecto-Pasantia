from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.stations import router as stations_router
from app.api.v1.bars import router as bars_router
from app.api.v1.circuits import router as circuits_router
from app.api.v1.sub_circuits import router as sub_circuits_router
from app.api.v1.users import router as users_router
from app.api.v1.requests import router as requests_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.observations import router as observations_router
from app.api.v1.audit import router as audit_router
from app.api.v1.permissions import router as permissions_router
from app.api.v1.backups import router as backups_router
from app.api.v1.images import router as images_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(stations_router)
api_router.include_router(bars_router)
api_router.include_router(circuits_router)
api_router.include_router(sub_circuits_router)
api_router.include_router(users_router)
api_router.include_router(requests_router)
api_router.include_router(notifications_router)
api_router.include_router(observations_router)
api_router.include_router(audit_router)
api_router.include_router(permissions_router)
api_router.include_router(backups_router)
api_router.include_router(images_router)
api_router.include_router(reports_router)
