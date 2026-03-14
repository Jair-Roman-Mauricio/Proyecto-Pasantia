from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserBrief

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/me",
    response_model=UserBrief,
    summary="Obtener usuario actual",
    description="""
Retorna el perfil del usuario autenticado a partir del token JWT de Supabase.

El login se realiza directamente con Supabase Auth desde el frontend.
Este endpoint solo verifica que el token sea válido y retorna los datos de perfil.

**Header requerido:**
```
Authorization: Bearer <supabase_access_token>
```
""",
    response_description="Datos del usuario autenticado (id, username, nombre completo, rol)",
    responses={
        401: {"description": "Token inválido, expirado o usuario no registrado en el sistema"},
    },
)
def get_me(current_user: User = Depends(get_current_user)):
    return UserBrief(
        id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
    )
