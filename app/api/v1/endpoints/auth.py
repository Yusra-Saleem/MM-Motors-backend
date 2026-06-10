from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, MeUpdateRequest, RegisterRequest
from app.services.auth import authenticate_user, current_user_dependency, register_user
from app.services.users import serialize_user, update_password
from app.services.response_envelope import success_response

router = APIRouter()

@router.post("/register", response_model=dict)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Standard registration endpoint. Syncs with Supabase Auth and local DB.
    """
    user = register_user(db, payload)
    return success_response(serialize_user(db, user), "User registered successfully")

@router.post("/login", response_model=dict)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint. Returns Supabase session tokens and local user profile.
    """
    user, session = authenticate_user(db, payload.email, payload.password)
    
    return success_response({
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "user": serialize_user(db, user),
    }, "Logged in successfully")

@router.get("/me", response_model=dict)
def me(current_user: User = Depends(current_user_dependency), db: Session = Depends(get_db)):
    """
    Returns the currently authenticated user's profile.
    """
    return success_response(serialize_user(db, current_user), "Profile retrieved")

@router.patch("/me", response_model=dict)
def update_me(payload: MeUpdateRequest, current_user: User = Depends(current_user_dependency), db: Session = Depends(get_db)):
    """
    Updates the current user's profile information.
    """
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return success_response(serialize_user(db, current_user), "Profile updated successfully")

@router.patch("/me/password", response_model=dict)
def change_password(payload: ChangePasswordRequest, current_user: User = Depends(current_user_dependency), db: Session = Depends(get_db)):
    """
    Changes the current user's password in the local backup and potentially Supabase (not implemented here).
    """
    from app.core.security import verify_password

    if current_user.password_hash and not verify_password(payload.current_password, current_user.password_hash):
        raise AppError("Current password is invalid", 400)
    
    update_password(db, current_user, payload.new_password)
    return success_response(message="Password updated successfully")

@router.post("/logout", response_model=dict)
def logout(_: User = Depends(current_user_dependency)):
    """
    Logout endpoint. Session management is primarily client-side with Supabase.
    """
    return success_response(message="Logged out successfully")
