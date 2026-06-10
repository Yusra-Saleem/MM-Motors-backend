from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import AccountStatus, User, UserRole
from app.schemas.user import UserCreate, UserStatusUpdate, UserUpdate
from app.services.auth import require_roles
from app.services.orders import serialize_order
from app.services.payments import serialize_payment
from app.services.users import create_user, delete_user, get_user_or_404, list_user_orders, list_user_payments, list_users, serialize_user, serialize_user_detail, set_user_status, update_user
from app.services.response_envelope import success_response

router = APIRouter()


@router.get("", response_model=dict)
def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    query: str | None = Query(default=None, alias="search"),
    role: UserRole | None = None,
    status: AccountStatus | None = None,
    sort_by: str = Query(default="newest", alias="sortBy"),
    sort_dir: str = Query(default="desc", alias="sortDir", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    effective_page_size = limit or page_size
    payload = list_users(db, page, effective_page_size, query, role, status, sort_by, sort_dir)
    payload["meta"]["pageSize"] = effective_page_size
    payload["meta"]["page_size"] = effective_page_size
    payload["meta"]["limit"] = effective_page_size
    return success_response(payload, "Users retrieved")


@router.post("", response_model=dict)
def create_user_admin(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    user = create_user(db, payload)
    return success_response(serialize_user(db, user), "User created")


@router.get("/{user_id}", response_model=dict)
def get_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    user = get_user_or_404(db, user_id)
    return success_response(serialize_user_detail(db, user), "User retrieved")


@router.get("/{user_id}/orders", response_model=dict)
def get_user_orders(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    user = get_user_or_404(db, user_id)
    effective_page_size = limit or page_size
    items, total = list_user_orders(db, user.id, page, effective_page_size)
    return success_response({
        "items": [serialize_order(item) for item in items],
        "meta": {
            "page": page,
            "pageSize": effective_page_size,
            "page_size": effective_page_size,
            "limit": effective_page_size,
            "total": total,
            "totalPages": max(1, -(-total // effective_page_size)),
            "total_pages": max(1, -(-total // effective_page_size)),
        },
    }, "User orders retrieved")


@router.get("/{user_id}/payments", response_model=dict)
def get_user_payments(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    user = get_user_or_404(db, user_id)
    effective_page_size = limit or page_size
    items, total = list_user_payments(db, user.id, page, effective_page_size)
    return success_response({
        "items": [serialize_payment(item) for item in items],
        "meta": {
            "page": page,
            "pageSize": effective_page_size,
            "page_size": effective_page_size,
            "limit": effective_page_size,
            "total": total,
            "totalPages": max(1, -(-total // effective_page_size)),
            "total_pages": max(1, -(-total // effective_page_size)),
        },
    }, "User payments retrieved")


@router.patch("/{user_id}", response_model=dict)
def patch_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    user = get_user_or_404(db, user_id)
    updated = update_user(db, user, payload)
    return success_response(serialize_user(db, updated), "User updated")


@router.patch("/{user_id}/status", response_model=dict)
def patch_user_status(user_id: str, payload: UserStatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    user = get_user_or_404(db, user_id)
    updated = set_user_status(db, user, payload.status)
    return success_response(serialize_user(db, updated), "User status updated")


@router.delete("/{user_id}", response_model=dict)
def remove_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    user = get_user_or_404(db, user_id)
    delete_user(db, user)
    return success_response(message="User deleted")
