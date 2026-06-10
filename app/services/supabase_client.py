from supabase import create_client, Client
from app.core.config import settings

# Create a singleton Supabase client using the service role key (full access).
# For client‑side usage (public) you would use the anon key instead.
_supabase_client: Client | None = None

def get_supabase() -> Client:
    """Return a cached Supabase client instance.

    The client is lazily created on first use. It reads the URL and key from
    the ``settings`` object which pulls values from the ``.env`` file.
    """
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError(
                "Supabase configuration is missing – check SUPABASE_URL and SUPABASE_KEY in .env"
            )
        _supabase_client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
    return _supabase_client

# Optional helper for storage bucket access
def get_storage_bucket(bucket_name: str = settings.supabase_storage_bucket) -> "supabase.storage.StorageBucket":
    """Convenient access to a Supabase storage bucket.

    The bucket name defaults to the one defined in ``settings.supabase_storage_bucket``.
    """
    client = get_supabase()
    return client.storage.from_(bucket_name)
