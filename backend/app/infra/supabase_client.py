"""Supabase client configuration and initialization."""

from typing import Optional

from supabase import Client, create_client

from app.core.settings import get_settings


class SupabaseClient:
    """Singleton Supabase client."""

    _instance: Client | None = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance."""
        if cls._instance is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase URL and key must be set in environment variables")
            
            cls._instance = create_client(
                str(settings.supabase_url),
                str(settings.supabase_key)
            )
        return cls._instance