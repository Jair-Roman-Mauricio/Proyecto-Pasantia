from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserBrief
from app.subest_client import get_public_client
from app.utils.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    import traceback
    try:
        client = get_public_client()
        result = client.rpc("get_user_by_username", {"p_username": form.username}).execute()
        users = result.data
        print(f"[LOGIN] users={users}")
        if not users:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

        user = users[0]
        password_hash = user.get("password_hash")
        ok = verify_password(form.password, password_hash) if password_hash else False
        print(f"[LOGIN] password_hash={password_hash[:10] if password_hash else None} verify={ok}")
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

        if user.get("status") != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

        token = create_access_token({"sub": user["id"], "role": user["role"], "username": user["username"]})
        print(f"[LOGIN] token generado ok")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        import sys
        traceback.print_exc()
        sys.stdout.flush()
        return {"error": str(e), "type": type(e).__name__}


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
