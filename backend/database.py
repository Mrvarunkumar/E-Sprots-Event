"""
Supabase client — provides two clients:
  • db_client  → uses anon key (public / row-level security applies)
  • admin_db   → uses service_role key (bypasses RLS, for admin operations)
"""
from supabase import create_client, Client
from config import settings


def get_supabase() -> Client:
    """Public client — obeys RLS policies."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_admin_supabase() -> Client:
    """Admin/service-role client — bypasses RLS. Use only in protected routes."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# Module-level singletons (reused across requests)
db_client: Client = get_supabase()
admin_db: Client = get_admin_supabase()
