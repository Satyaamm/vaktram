"""Supabase client initialisation."""

from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

_client: Client | None = None


def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _client
