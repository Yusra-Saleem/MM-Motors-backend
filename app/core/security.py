from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    if not hashed_password:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

# Manual token generation is deprecated as we are moving to Supabase Auth.
# Kept for reference or internal use if needed, but not for external clients.

def create_access_token(subject: str, role: str) -> str:
    to_encode = {
        "sub": str(subject),
        "role": role,
        "token_type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.algorithm)
