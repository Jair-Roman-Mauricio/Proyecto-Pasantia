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


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar todos los usuarios",
    description="Retorna la lista completa de usuarios registrados en el sistema, ordenados por ID. Solo accesible por administradores.",
    response_description="Lista de usuarios con sus datos completos",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
    },
)
def get_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.id).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener un usuario por ID",
    description="Retorna los datos completos de un usuario específico. Solo accesible por administradores.",
    response_description="Datos del usuario solicitado",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post(
    "",
    response_model=UserResponse,
    summary="Crear nuevo usuario",
    description="""
Crea un nuevo usuario en el sistema. Solo accesible por administradores.

**Roles disponibles:**
- `admin` — Acceso total al sistema
- `opersac` — Acceso limitado, controlado por permisos

Al crear un usuario con rol `opersac`, se le asignan automáticamente **todos los permisos habilitados** por defecto.
El administrador puede luego ajustar los permisos individualmente en `PUT /permissions/users/{user_id}`.

La acción queda registrada en el log de auditoría.
""",
    response_description="Datos del usuario recién creado",
    responses={
        400: {"description": "El nombre de usuario ya existe, o el rol es inválido"},
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
    },
)
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


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="""
Actualiza los datos de un usuario existente. Solo accesible por administradores.

**Campos actualizables:**
- `full_name` — Nombre completo
- `password` — Nueva contraseña (se hashea automáticamente)
- `status` — Estado del usuario: `active`, `inactive`, `reported`

Solo los campos incluidos en el body serán actualizados. La acción queda registrada en auditoría.
""",
    response_description="Datos del usuario actualizado",
    responses={
        400: {"description": "Estado inválido"},
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
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


@router.delete(
    "/{user_id}",
    summary="Eliminar usuario",
    description="Elimina permanentemente un usuario del sistema. No se puede eliminar el propio usuario autenticado. La acción queda registrada en auditoría. Solo accesible por administradores.",
    response_description="Confirmación de eliminación",
    responses={
        400: {"description": "No se puede eliminar el propio usuario"},
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    username = user.username
    db.delete(user)
    safe_commit(db)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="DELETE_USER",
        entity_type="user",
        entity_id=user_id,
        details={"username": username},
    )

    return {"message": "Usuario eliminado exitosamente"}
