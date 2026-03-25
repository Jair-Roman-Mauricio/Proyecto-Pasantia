from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.config import settings

_subest_client: Client | None = None
_public_client: Client | None = None


def get_subest_client() -> Client:
    """Cliente Supabase para las tablas de la app (schema public)."""
    global _subest_client
    if _subest_client is None:
        _subest_client = create_client(
            supabase_url=settings.SUBEST_SUPABASE_URL,
            supabase_key=settings.SUBEST_SUPABASE_KEY,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
    return _subest_client


def get_public_client() -> Client:
    """Cliente Supabase para el schema public (RPC functions)."""
    global _public_client
    if _public_client is None:
        _public_client = create_client(
            supabase_url=settings.SUBEST_SUPABASE_URL,
            supabase_key=settings.SUBEST_SUPABASE_KEY,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
    return _public_client
