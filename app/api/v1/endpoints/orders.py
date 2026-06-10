from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.order import OrderStatus, PaymentStatus
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderUpdate
from app.services.auth import current_user_dependency, require_roles
from app.services.orders import create_order, delete_order, get_order_or_404, list_order_payments, list_orders, serialize_order, serialize_order_detail, update_order, update_order_status
from app.services.response_envelope import success_response

router = APIRouter()


@router.get("", response_model=dict)
def get_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    query: str | None = Query(default=None, alias="search"),
    user_id: str | None = None,
    car_id: str | None = None,
    status: OrderStatus | None = None,
    payment_status: PaymentStatus | None = None,
    sort_by: str = Query(default="newest", alias="sortBy"),
    sort_dir: str = Query(default="desc", alias="sortDir", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user_dependency),
):
    effective_page_size = limit or page_size
    if current_user.role != UserRole.admin:
        user_id = current_user.id
    items, total = list_orders(db, page, effective_page_size, query, user_id, status, payment_status, sort_by, sort_dir, car_id)
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
    }, "Orders retrieved")


@router.post("", response_model=dict)
def post_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin, UserRole.dealer))):
    order = create_order(db, payload, current_user)
    return success_response(serialize_order(order), "Order created")


@router.get("/{order_id}", response_model=dict)
def get_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(current_user_dependency)):
    order = get_order_or_404(db, order_id)
    if current_user.role != UserRole.admin and order.user_id != current_user.id:
        from app.core.errors import AppError

        raise AppError("Forbidden", 403)
    return success_response(serialize_order_detail(db, order), "Order retrieved")


@router.get("/{order_id}/payments", response_model=dict)
def get_order_payments(
    order_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user_dependency),
):
    order = get_order_or_404(db, order_id)
    if current_user.role != UserRole.admin and order.user_id != current_user.id:
        from app.core.errors import AppError

        raise AppError("Forbidden", 403)
    effective_page_size = limit or page_size
    all_items = list_order_payments(db, order.id)
    total = len(all_items)
    items = all_items[(page - 1) * effective_page_size : page * effective_page_size]
    return success_response({
        "items": [
            {
                "id": payment.id,
                "user_id": payment.user_id,
                "userId": payment.user_id,
                "order_id": payment.order_id,
                "orderId": payment.order_id,
                "amount": payment.amount,
                "date": payment.date,
                "method": payment.method,
                "status": payment.status,
                "notes": payment.notes,
                "transaction_metadata": payment.transaction_metadata or {},
                "transactionMetadata": payment.transaction_metadata or {},
            }
            for payment in items
        ],
        "meta": {
            "page": page,
            "pageSize": effective_page_size,
            "page_size": effective_page_size,
            "limit": effective_page_size,
            "total": total,
            "totalPages": max(1, -(-total // effective_page_size)),
            "total_pages": max(1, -(-total // effective_page_size)),
        },
    }, "Order payments retrieved")


@router.patch("/{order_id}", response_model=dict)
def patch_order(order_id: str, payload: OrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin))):
    order = get_order_or_404(db, order_id)
    return success_response(serialize_order(update_order(db, order, payload, current_user)), "Order updated")


@router.patch("/{order_id}/status", response_model=dict)
def patch_order_status(order_id: str, payload: OrderStatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    order = get_order_or_404(db, order_id)
    return success_response(serialize_order(update_order_status(db, order, payload.status)), "Order status updated")


@router.delete("/{order_id}", response_model=dict)
def remove_order(order_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    order = get_order_or_404(db, order_id)
    delete_order(db, order)
    return success_response(message="Order deleted")
