from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.permission import Permission
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.audit_service import AuditService
from app.utils.security import hash_password
from app.utils.constants import PERMISSION_FEATURES
from app.utils.db_helpers import safe_commit

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.id).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    if data.role not in ("admin", "opersac"):
        raise HTTPException(status_code=400, detail="Rol invalido")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        status="active",
    )
    db.add(user)
    safe_commit(db)
    db.refresh(user)

    # Create default permissions for opersac users
    if user.role == "opersac":
        for feature in PERMISSION_FEATURES:
            perm = Permission(
                user_id=user.id,
                feature_key=feature,
                is_allowed=True,
            )
            db.add(perm)
        safe_commit(db)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CREATE_USER",
        entity_type="user",
        entity_id=user.id,
        details={"username": user.username, "role": user.role},
    )

    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.status is not None:
        if data.status not in ("active", "inactive", "reported"):
            raise HTTPException(status_code=400, detail="Estado invalido")
        user.status = data.status
    if data.password is not None:
        user.password_hash = hash_password(data.password)

    safe_commit(db)
    db.refresh(user)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="UPDATE_USER",
        entity_type="user",
        entity_id=user.id,
        details={"updated_fields": [k for k, v in data.model_dump(exclude_unset=True).items()]},
    )

    return user
