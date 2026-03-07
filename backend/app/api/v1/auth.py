from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserBrief
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="""
Autentica al usuario con sus credenciales y retorna un token JWT de acceso.

**El token debe incluirse en todas las solicitudes posteriores:**
```
Authorization: Bearer <access_token>
```

**Usuarios por defecto al iniciar el sistema:**
- `admin` / `admin123` — Administrador con acceso total
""",
    response_description="Token JWT y datos básicos del usuario autenticado",
    responses={
        401: {"description": "Credenciales incorrectas o usuario inactivo"},
    },
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = service.create_token(user)
    return TokenResponse(
        access_token=token,
        user=UserBrief(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
        ),
    )


@router.get(
    "/me",
    response_model=UserBrief,
    summary="Obtener usuario actual",
    description="Retorna los datos del usuario autenticado a partir del token JWT. Útil para verificar si la sesión sigue activa.",
    response_description="Datos básicos del usuario autenticado (id, username, nombre completo, rol)",
    responses={
        401: {"description": "Token inválido, expirado o no proporcionado"},
    },
)
def get_me(current_user: User = Depends(get_current_user)):
    return UserBrief(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
    )
