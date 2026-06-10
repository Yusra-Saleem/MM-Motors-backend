from __future__ import annotations

from uuid import uuid4

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.order import Order
from app.models.payment import Payment, UserPaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.orders import recalc_orders_from_payments, sync_user_totals
from app.services.response_aliases import with_response_aliases


def _normalize_sort(sort_by: str | None, sort_dir: str | None) -> tuple[str, str]:
    normalized_sort = (sort_by or "newest").lower()
    normalized_dir = (sort_dir or "desc").lower()
    mapping = {
        "newest": ("date", "desc"),
        "oldest": ("date", "asc"),
        "amount_asc": ("amount", "asc"),
        "amount_desc": ("amount", "desc"),
    }
    if normalized_sort in {"date", "amount"}:
        return normalized_sort, "desc" if normalized_dir != "asc" else "asc"
    return mapping.get(normalized_sort, ("date", "desc"))


def serialize_payment(payment: Payment) -> dict:
    return with_response_aliases({
        "id": payment.id,
        "user_id": payment.user_id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "date": payment.date,
        "method": payment.method,
        "status": payment.status,
        "notes": payment.notes,
        "transaction_metadata": payment.transaction_metadata or {},
    })


def serialize_payment_detail(db: Session, payment: Payment) -> dict:
    user = db.query(User).filter(User.id == payment.user_id).first()
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    payload = serialize_payment(payment)
    payload["user"] = (
        {"id": user.id, "name": user.name, "email": user.email} if user else None
    )
    payload["order"] = (
        {
            "id": order.id,
            "user_id": order.user_id,
            "car_id": order.car_id,
            "car_name": order.car_name,
            "car_cid": order.car_cid,
            "total_amount": order.total_amount,
            "paid_amount": order.paid_amount,
            "balance_amount": order.balance_amount,
            "payment_status": order.payment_status,
            "status": order.status,
            "date": order.date,
        }
        if order
        else None
    )
    return with_response_aliases(payload)


def list_payments(
    db: Session,
    page: int,
    page_size: int,
    query: str | None,
    user_id: str | None,
    order_id: str | None,
    status: UserPaymentStatus | None,
    sort_by: str,
    sort_dir: str,
):
    normalized_sort, normalized_dir = _normalize_sort(sort_by, sort_dir)
    qs = db.query(Payment)
    if query:
        like = f"%{query}%"
        qs = qs.filter(
            or_(
                Payment.id.ilike(like),
                Payment.method.ilike(like),
                Payment.notes.ilike(like),
                cast(Payment.transaction_metadata, String).ilike(like),
            )
        )
    if user_id:
        qs = qs.filter(Payment.user_id == user_id)
    if order_id:
        qs = qs.filter(Payment.order_id == order_id)
    if status:
        qs = qs.filter(Payment.status == status)
    sort_column = getattr(Payment, normalized_sort, Payment.date)
    qs = qs.order_by(sort_column.desc() if normalized_dir == "desc" else sort_column.asc())
    total = qs.order_by(None).count()
    items = qs.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_payment_or_404(db: Session, payment_id: str) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise AppError("Payment not found", 404)
    return payment


def _resolve_order(db: Session, order_id: str | None, current_order_id: str | None = None) -> Order:
    resolved_order_id = order_id or current_order_id
    if not resolved_order_id:
        raise AppError("order_id is required", 400)
    order = db.query(Order).filter(Order.id == resolved_order_id).first()
    if not order:
        raise AppError("Order not found", 404)
    return order


def create_payment(db: Session, payload: PaymentCreate, actor: User | None = None) -> Payment:
    order = _resolve_order(db, payload.order_id)
    payment = Payment(
        id=payload.id or f"PAY-{uuid4().hex[:8].upper()}",
        user_id=order.user_id,
        order_id=order.id,
        amount=payload.amount,
        date=payload.date,
        method=payload.method,
        status=payload.status,
        notes=payload.notes,
        transaction_metadata=payload.transaction_metadata,
        created_by=actor.id if actor else None,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    recalc_orders_from_payments(db, order.id)
    return payment


def update_payment(db: Session, payment: Payment, payload: PaymentUpdate, actor: User | None = None) -> Payment:
    old_order_id = payment.order_id
    old_user_id = payment.user_id
    data = payload.model_dump(exclude_unset=True)

    if "order_id" in data:
        order = _resolve_order(db, payload.order_id, payment.order_id)
        payment.order_id = order.id
        payment.user_id = order.user_id
    elif "user_id" in data:
        order = _resolve_order(db, None, payment.order_id)
        payment.user_id = order.user_id

    for field, value in data.items():
        if field in {"order_id", "user_id"}:
            continue
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    recalc_orders_from_payments(db, old_order_id)
    if payment.order_id != old_order_id:
        recalc_orders_from_payments(db, payment.order_id)
    if payment.user_id != old_user_id:
        sync_user_totals(db, old_user_id)
        sync_user_totals(db, payment.user_id)
    return payment


def delete_payment(db: Session, payment: Payment) -> None:
    order_id = payment.order_id
    user_id = payment.user_id
    db.delete(payment)
    db.commit()
    recalc_orders_from_payments(db, order_id)
    sync_user_totals(db, user_id)
