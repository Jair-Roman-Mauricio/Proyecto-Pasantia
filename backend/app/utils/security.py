import httpx
from jose import JWTError, jwt

from app.config import settings

_jwks_cache: dict | None = None


def _get_jwks() -> dict:
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
