import httpx
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from app.config import settings


def verify_password(plain: str, stored: str) -> bool:
    return plain == stored


def create_access_token(data: dict, expires_minutes: int = 60 * 24) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload["iss"] = "linea1metro"
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

_jwks_cache: dict | None = None


def _get_jwks() -> dict:
    """Descarga y cachea el JWKS de Supabase para verificar tokens ES256/RS256.

    Llama a `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` la primera vez y
    almacena el resultado en `_jwks_cache`. Las llamadas siguientes devuelven
    la caché sin volver a realizar el request HTTP.

    Returns:
        dict con la clave ``"keys"`` que contiene la lista de JWK públicas.
        Si la descarga falla devuelve ``{"keys": []}``.
    """
    global _jwks_cache
    if _jwks_cache is None:
        url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        print(f"[SUPABASE JWKS] Fetching from {url}")
        try:
            resp = httpx.get(url, timeout=5)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            print(f"[SUPABASE JWKS] OK — keys: {[k.get('kid') for k in _jwks_cache.get('keys', [])]}")
        except Exception as e:
            print(f"[SUPABASE JWKS] ERROR: {e}")
            _jwks_cache = {"keys": []}
    return _jwks_cache


def decode_supabase_token(token: str) -> dict | None:
    """Verifica y decodifica un JWT emitido por Supabase Auth.

    Estrategia de verificación:
    - Si el header del token indica ``alg=HS256``, decodifica usando
      ``SUPABASE_JWT_SECRET`` (modo local / tests).
    - Si el algoritmo es ES256 o RS256 (producción), descarga el JWKS de
      Supabase y selecciona la clave pública cuyo ``kid`` coincida con el
      header del token.

    Args:
        token: JWT en formato compacto (header.payload.signature).

    Returns:
        Diccionario con el payload del token si la firma es válida,
        o ``None`` si el token está expirado, es inválido o no hay clave.
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        kid = header.get("kid")
        print(f"[SUPABASE JWT] alg={alg} kid={kid}")

        if alg == "HS256":
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            jwks = _get_jwks()
            keys = jwks.get("keys", [])
            # Buscar la clave que coincida con kid
            key = next((k for k in keys if k.get("kid") == kid), keys[0] if keys else None)
            if not key:
                print("[SUPABASE JWT] No key found in JWKS")
                return None
            print(f"[SUPABASE JWT] Using key kid={key.get('kid')} kty={key.get('kty')}")
            payload = jwt.decode(
                token,
                key,
                algorithms=[alg],
                options={"verify_aud": False},
            )

        return payload
    except JWTError as e:
        print(f"[SUPABASE JWT ERROR] {e}")
        return None
