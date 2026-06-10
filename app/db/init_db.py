import os
import logging
from sqlalchemy.exc import OperationalError

from app.services.seed import seed_database


def init_db() -> None:
    # Skip database initialization if the DATABASE_URL is not properly configured.
    # This prevents startup crashes during local development when Supabase DB credentials are absent.
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url or "YOUR_PASSWORD" in db_url or "YOUR_PROJECT_REF" in db_url:
        logging.info("Skipping database initialization: DATABASE_URL not configured.")
        return

    if os.getenv("MM_MOTORS_BOOTSTRAP_SEED", "").lower() in {"1", "true", "yes"}:
        try:
            seed_database()
        except OperationalError as db_err:
            logging.error("Database initialization failed: %s", db_err)
        except Exception as exc:
            logging.exception("Unexpected error during database seed: %s", exc)
