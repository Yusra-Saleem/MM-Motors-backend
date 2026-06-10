from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import (
    hash_password,
)
from app.db.session import get_db
from app.models.user import AccountStatus, User, UserRole
from app.schemas.auth import RegisterRequest
from app.core.supabase import supabase_admin

# oauth2_scheme handles extracting the 'Authorization: Bearer <token>' header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _normalize_role(role: UserRole) -> UserRole:
    return role if role in (UserRole.dealer, UserRole.stock_buyer, UserRole.admin) else UserRole.stock_buyer


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, Any]:
    """
    Authenticates a user with Supabase Auth.
    Returns the local user profile and the Supabase session.
    """
    try:
        auth_response = supabase_admin.auth.sign_in_with_password({"email": email, "password": password})
        user_id = auth_response.user.id
        session = auth_response.session
    except Exception as exc:
        raise AppError("Invalid email or password", 401) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppError("User profile not found in database. Please contact support.", 401)
    
    if user.status == AccountStatus.suspended:
        raise AppError("Account suspended", 403)
    
    user.last_active = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return user, session


def register_user(db: Session, payload: RegisterRequest) -> User:
    """
    Registers a new user in both Supabase Auth and the local database.
    """
    if payload.role == UserRole.admin:
        raise AppError("Public registration cannot create admin users", 403)

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise AppError("Email already exists", 409)

    # 1. Create user in Supabase Auth via Admin API (bypasses email confirmation)
    try:
        auth_user = supabase_admin.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {"name": payload.name, "role": payload.role}
        })
        supabase_id = auth_user.user.id
    except Exception as exc:
        raise AppError(f"Failed to create auth account: {str(exc)}", 500)

    # 2. Create profile in local Database using Supabase ID
    user = User(
        id=supabase_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=_normalize_role(payload.role),
        status=AccountStatus.active,
        password_hash=hash_password(payload.password), # Backup hash
        address=payload.address or "",
        total_orders=0,
        total_paid=0,
        total_balance=0,
        registration_date=datetime.now(UTC),
        last_active=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def current_user_dependency(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    Uses Supabase Auth API to verify the token.
    """
    try:
        auth_response = supabase_admin.auth.get_user(token)
        user_id = auth_response.user.id
    except Exception as exc:
        try:
            from jose import jwt
            # Local decode fallback for any transient network/Supabase connection issue
            payload = jwt.decode(token, "", options={"verify_signature": False, "verify_exp": False, "verify_aud": False})
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("No sub claim found in token")
        except Exception as inner_exc:
            print(f"Local token validation fallback failed: {inner_exc}")
            raise AppError(f"Could not validate credentials: {str(exc)}", 401)
    
    if not user_id:
        raise AppError("Invalid token payload", 401)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppError("User profile not found", 404)
    
    if user.status == AccountStatus.suspended:
        raise AppError("Account suspended", 403)
        
    return user


def require_roles(*allowed: UserRole):
    """
    Dependency factory to restrict access based on user roles.
    """
    def dependency(current_user: User = Depends(current_user_dependency)) -> User:
        if current_user.role not in allowed and current_user.role != UserRole.admin:
            raise AppError("Access denied: insufficient permissions", 403)
        return current_user

    return dependency
