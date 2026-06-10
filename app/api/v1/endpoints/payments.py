from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.payment import UserPaymentStatus
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.auth import current_user_dependency, require_roles
from app.services.payments import create_payment, delete_payment, get_payment_or_404, list_payments, serialize_payment, serialize_payment_detail, update_payment
from app.services.response_envelope import success_response

router = APIRouter()


@router.get("", response_model=dict)
def get_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    query: str | None = Query(default=None, alias="search"),
    user_id: str | None = None,
    order_id: str | None = None,
    status: UserPaymentStatus | None = None,
    sort_by: str = Query(default="newest", alias="sortBy"),
    sort_dir: str = Query(default="desc", alias="sortDir", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user_dependency),
):
    effective_page_size = limit or page_size
    if current_user.role != UserRole.admin:
        user_id = current_user.id
    items, total = list_payments(db, page, effective_page_size, query, user_id, order_id, status, sort_by, sort_dir)
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
    }, "Payments retrieved")


@router.get("/history", response_model=dict)
def payment_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    query: str | None = Query(default=None, alias="search"),
    order_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user_dependency),
):
    effective_page_size = limit or page_size
    items, total = list_payments(db, page, effective_page_size, query, current_user.id if current_user.role != UserRole.admin else None, order_id, None, "newest", "desc")
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
    }, "Payment history retrieved")


@router.post("", response_model=dict)
def post_payment(payload: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin))):
    payment = create_payment(db, payload, current_user)
    return success_response(serialize_payment(payment), "Payment created")


@router.get("/{payment_id}", response_model=dict)
def get_payment(payment_id: str, db: Session = Depends(get_db), current_user: User = Depends(current_user_dependency)):
    payment = get_payment_or_404(db, payment_id)
    if current_user.role != UserRole.admin and payment.user_id != current_user.id:
        from app.core.errors import AppError

        raise AppError("Forbidden", 403)
    return success_response(serialize_payment_detail(db, payment), "Payment retrieved")


@router.patch("/{payment_id}", response_model=dict)
def patch_payment(payment_id: str, payload: PaymentUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin))):
    payment = get_payment_or_404(db, payment_id)
    return success_response(serialize_payment(update_payment(db, payment, payload, current_user)), "Payment updated")


@router.delete("/{payment_id}", response_model=dict)
def remove_payment(payment_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    payment = get_payment_or_404(db, payment_id)
    delete_payment(db, payment)
    return success_response(message="Payment deleted")
