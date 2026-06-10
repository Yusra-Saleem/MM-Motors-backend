from sqlalchemy.engine import URL, make_url

from app.core.config import settings


def _repair_database_url(raw_url: str) -> str:
    # Supabase passwords sometimes get pasted with a literal "@" and break URL parsing.
    # Re-encode the password segment if the parsed host is malformed.
    url = make_url(raw_url)
    if "@" not in (url.host or ""):
        return raw_url

    scheme, remainder = raw_url.split("://", 1)
    credentials, host_part = remainder.rsplit("@", 1)
    if ":" not in credentials:
        return raw_url

    username, password = credentials.split(":", 1)
    from urllib.parse import quote

    repaired = f"{scheme}://{username}:{quote(password, safe='')}@{host_part}"
    return repaired


def get_database_url() -> str:
    raw_url = _repair_database_url(settings.database_url)
    url: URL = make_url(raw_url)

    if url.get_backend_name() != "postgresql":
        raise RuntimeError("DATABASE_URL must point to a PostgreSQL database.")

    if url.drivername != "postgresql+psycopg":
        url = url.set(drivername="postgresql+psycopg")

    query = dict(url.query)
    query.setdefault("sslmode", "require")
    query.setdefault("application_name", "mm-motors-api")
    url = url.update_query_dict(query)

    return url.render_as_string(hide_password=False)
