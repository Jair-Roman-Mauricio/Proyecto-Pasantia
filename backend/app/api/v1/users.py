import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.permission import Permission
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.audit_service import AuditService
from app.utils.supabase_admin import create_supabase_auth_user, delete_supabase_auth_user, update_supabase_auth_user
from app.utils.constants import PERMISSION_FEATURES
from app.utils.db_helpers import safe_commit

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar todos los usuarios",
    description="Retorna la lista completa de usuarios registrados en el sistema. Solo accesible por administradores.",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def get_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener un usuario por ID",
    description="Retorna los datos completos de un usuario específico. Solo accesible por administradores.",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
def get_user(
    user_id: uuid.UUID,
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
    status_code=201,
    summary="Crear nuevo usuario",
    description="""
Crea un nuevo usuario en el sistema y en Supabase Auth. Solo accesible por administradores.

El usuario se registra en Supabase usando `{username}@linea1metro.internal` como email.
El `id` del perfil corresponde al UUID asignado por Supabase Auth.

Al crear un usuario con rol `opersac`, se le asignan todos los permisos habilitados por defecto.
""",
    responses={
        400: {"description": "El nombre de usuario ya existe, o el rol es inválido"},
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
    },
)
async def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    if data.role not in ("admin", "opersac"):
        raise HTTPException(status_code=400, detail="Rol invalido")

    email = f"{data.username}@linea1metro.internal"
    try:
        supabase_user = await create_supabase_auth_user(
            email=email,
            password=data.password,
            username=data.username,
            role=data.role,
            full_name=data.full_name,
            phone=data.phone or "",
            contact_email=data.email or "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear usuario en Supabase: {str(e)}")

    user = User(
        id=uuid.UUID(supabase_user["id"]),
        username=data.username,
        full_name=data.full_name,
        role=data.role,
        status="active",
    )
    db.add(user)
    safe_commit(db)
    db.refresh(user)

    if user.role == "opersac":
        for feature in PERMISSION_FEATURES:
            perm = Permission(user_id=user.id, feature_key=feature, is_allowed=True)
            db.add(perm)
        safe_commit(db)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CREATE_USER",
        entity_type="user",
        entity_id=str(user.id),
        details={"username": user.username, "role": user.role},
    )

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="""
Actualiza los datos de perfil de un usuario existente. Solo accesible por administradores.

**Campos actualizables:** `full_name`, `status`

Para cambiar la contraseña, usar el panel de Supabase Auth o la API de Supabase.
""",
    responses={
        400: {"description": "Estado inválido"},
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
async def update_user(
    user_id: uuid.UUID,
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

    if data.phone is not None or data.email is not None:
        try:
            await update_supabase_auth_user(
                user_uuid=str(user.id),
                phone=data.phone or "",
                contact_email=data.email or "",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar en Supabase: {str(e)}")

    safe_commit(db)
    db.refresh(user)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="UPDATE_USER",
        entity_type="user",
        entity_id=str(user.id),
        details={"updated_fields": [k for k, v in data.model_dump(exclude_unset=True).items()]},
    )

    return user


@router.delete(
    "/{user_id}",
    summary="Eliminar usuario",
    description="Elimina el usuario del sistema y de Supabase Auth. No se puede eliminar el propio usuario. Solo accesible por administradores.",
    responses={
        400: {"description": "No se puede eliminar el propio usuario"},
        401: {"description": "No autenticado"},
        403: {"description": "Se requiere rol admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
async def delete_user(
    user_id: uuid.UUID,
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

    try:
        await delete_supabase_auth_user(str(user_id))
    except Exception:
        pass

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="DELETE_USER",
        entity_type="user",
        entity_id=str(user_id),
        details={"username": username},
    )

    return {"message": "Usuario eliminado exitosamente"}
