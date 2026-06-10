from app.services.supabase_client import get_supabase

# Expose a singleton Supabase client for admin operations.
# This client uses the service role key, giving full access to Supabase Auth
# and bypassing RLS. It should only be used server‑side.

supabase_admin = get_supabase()
