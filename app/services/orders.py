from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.car import Car
from app.models.favorite import Favorite
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment, UserPaymentStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.response_aliases import with_response_aliases
from app.services.cars import sync_car_rankings


def _sync_payment_state(order: Order) -> None:
    order.balance_amount = max(0, order.total_amount - order.paid_amount)
    if order.balance_amount <= 0:
        order.payment_status = PaymentStatus.paid
        return

    if order.paid_amount > 0:
        order.payment_status = PaymentStatus.partial
        return

    order.payment_status = PaymentStatus.unpaid


def _car_snapshot(car: Car) -> dict:
    return {
        "id": car.id,
        "cid": car.cid,
        "chassis_number": car.chassis_number,
        "make": car.make,
        "name": car.name,
        "package": car.package,
        "year": car.year,
        "import_year": car.import_year,
        "price": car.price,
        "status": car.status,
        "mileage": car.mileage,
        "transmission": car.transmission,
        "fuel_type": car.fuel_type,
        "body_type": car.body_type,
        "drive_type": car.drive_type,
        "exterior_color": car.exterior_color,
        "grade": car.grade,
        "engine_type": car.engine_type,
        "description": car.description,
        "features": car.features or [],
        "images": car.images or [],
        "thumbnail": car.thumbnail,
        "specifications": car.specifications or {},
        "featured_flag": car.featured_flag,
        "priority_score": car.priority_score,
        "engagement_score": car.engagement_score,
        "created_at": car.created_at.isoformat() if isinstance(car.created_at, datetime) else car.created_at,
        "updated_at": car.updated_at.isoformat() if isinstance(car.updated_at, datetime) else car.updated_at,
    }


def _get_initial_payment(db: Session, order_id: str) -> Payment | None:
    payments = db.query(Payment).filter(Payment.order_id == order_id).all()
    for payment in payments:
        metadata = payment.transaction_metadata or {}
        if metadata.get("source") == "order_initial":
            return payment
    return None


def _sync_initial_payment(
    db: Session,
    order: Order,
    target_paid_amount: float | None,
    payment_method: str | None = None,
    payment_date: datetime | None = None,
) -> None:
    if target_paid_amount is None:
        return

    manual_payments = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .all()
    )
    manual_confirmed = sum(
        payment.amount
        for payment in manual_payments
        if payment.status == UserPaymentStatus.confirmed
        and (payment.transaction_metadata or {}).get("source") != "order_initial"
    )

    initial_payment = _get_initial_payment(db, order.id)
    initial_amount = max(0, target_paid_amount - manual_confirmed)

    if initial_amount <= 0:
        if initial_payment:
            db.delete(initial_payment)
            db.commit()
        return

    if initial_payment:
        initial_payment.amount = initial_amount
        initial_payment.method = payment_method or initial_payment.method
        initial_payment.date = payment_date or initial_payment.date
        initial_payment.status = UserPaymentStatus.confirmed
        initial_payment.transaction_metadata = {
            **(initial_payment.transaction_metadata or {}),
            "source": "order_initial",
        }
        db.commit()
        return

    payment = Payment(
        id=f"PAY-{uuid4().hex[:8].upper()}",
        user_id=order.user_id,
        order_id=order.id,
        amount=initial_amount,
        date=payment_date or order.date,
        method=payment_method or order.payment_method,
        status=UserPaymentStatus.confirmed,
        notes="Initial order payment",
        transaction_metadata={"source": "order_initial"},
    )
    db.add(payment)
    db.commit()


def _normalize_sort(sort_by: str | None, sort_dir: str | None) -> tuple[str, str]:
    normalized_sort = (sort_by or "newest").lower()
    normalized_dir = (sort_dir or "desc").lower()
    mapping = {
        "newest": ("date", "desc"),
        "oldest": ("date", "asc"),
        "amount_asc": ("total_amount", "asc"),
        "amount_desc": ("total_amount", "desc"),
        "paid_asc": ("paid_amount", "asc"),
        "paid_desc": ("paid_amount", "desc"),
        "balance_asc": ("balance_amount", "asc"),
        "balance_desc": ("balance_amount", "desc"),
    }
    if normalized_sort in {"date", "total_amount", "paid_amount", "balance_amount"}:
        return normalized_sort, "desc" if normalized_dir != "asc" else "asc"
    return mapping.get(normalized_sort, ("date", "desc"))


def serialize_order(order: Order) -> dict:
    return with_response_aliases({
        "id": order.id,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "car_id": order.car_id,
        "car_name": order.car_name,
        "car_cid": order.car_cid,
        "total_amount": order.total_amount,
        "paid_amount": order.paid_amount,
        "balance_amount": order.balance_amount,
        "payment_status": order.payment_status,
        "status": order.status,
        "date": order.date,
        "payment_method": order.payment_method,
        "notes": order.notes,
        "car_snapshot": order.car_snapshot or {},
    })


def serialize_order_detail(db: Session, order: Order) -> dict:
    user = db.query(User).filter(User.id == order.user_id).first()
    car = db.query(Car).filter(Car.id == order.car_id).first()
    payments = db.query(Payment).filter(Payment.order_id == order.id).order_by(Payment.date.desc()).all()
    payload = serialize_order(order)
    payload["user"] = (
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "status": user.status,
            "avatar": user.avatar,
            "address": user.address,
            "total_orders": user.total_orders,
            "total_paid": user.total_paid,
            "total_balance": user.total_balance,
            "registration_date": user.registration_date,
            "last_active": user.last_active,
            "favorites_count": db.query(Favorite).filter(Favorite.user_id == user.id).count(),
        }
        if user
        else None
    )
    payload["car"] = order.car_snapshot or (_car_snapshot(car) if car else None)
    payload["payments"] = [
        {
            "id": payment.id,
            "user_id": payment.user_id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "date": payment.date,
            "method": payment.method,
            "status": payment.status,
            "notes": payment.notes,
            "transaction_metadata": payment.transaction_metadata or {},
        }
        for payment in payments
    ]
    return with_response_aliases(payload)


def list_orders(
    db: Session,
    page: int,
    page_size: int,
    query: str | None,
    user_id: str | None,
    status: OrderStatus | None,
    payment_status: PaymentStatus | None,
    sort_by: str,
    sort_dir: str,
    car_id: str | None = None,
):
    normalized_sort, normalized_dir = _normalize_sort(sort_by, sort_dir)
    qs = db.query(Order)
    if query:
        like = f"%{query}%"
        qs = qs.filter(
            or_(
                Order.id.ilike(like),
                Order.customer_name.ilike(like),
                Order.car_name.ilike(like),
                Order.car_cid.ilike(like),
                Order.notes.ilike(like),
                cast(Order.payment_method, String).ilike(like),
            )
        )
    if user_id:
        qs = qs.filter(Order.user_id == user_id)
    if car_id:
        qs = qs.filter(Order.car_id == car_id)
    if status:
        qs = qs.filter(Order.status == status)
    if payment_status:
        qs = qs.filter(Order.payment_status == payment_status)
    sort_column = getattr(Order, normalized_sort, Order.date)
    qs = qs.order_by(sort_column.desc() if normalized_dir == "desc" else sort_column.asc())
    total = qs.order_by(None).count()
    items = qs.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_order_or_404(db: Session, order_id: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise AppError("Order not found", 404)
    return order


def create_order(db: Session, payload: OrderCreate, actor: User | None = None) -> Order:
    user = db.query(User).filter(User.id == payload.user_id).first()
    car = db.query(Car).filter(Car.id == payload.car_id).first()
    if not user:
        raise AppError("User not found", 404)
    if not car:
        raise AppError("Car not found", 404)

    order = Order(
        id=payload.id or f"ORD-{uuid4().hex[:8].upper()}",
        user_id=user.id,
        car_id=car.id,
        customer_name=payload.customer_name,
        car_name=car.name,
        car_cid=car.cid,
        total_amount=payload.total_amount,
        paid_amount=payload.paid_amount,
        balance_amount=max(0, payload.total_amount - payload.paid_amount),
        payment_status=payload.payment_status,
        status=payload.status,
        date=payload.date,
        payment_method=payload.payment_method,
        notes=payload.notes,
        car_snapshot=_car_snapshot(car),
        created_by=actor.id if actor else None,
    )
    _sync_payment_state(order)
    db.add(order)
    db.commit()
    db.refresh(order)
    _sync_initial_payment(db, order, payload.paid_amount, payload.payment_method, payload.date)
    recalc_orders_from_payments(db, order.id)
    sync_car_rankings(db, order.car_id)
    sync_user_totals(db, user.id)
    return order


def update_order(db: Session, order: Order, payload: OrderUpdate, actor: User | None = None) -> Order:
    old_user_id = order.user_id
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(order, field, value)

    if "car_id" in data:
        car = db.query(Car).filter(Car.id == order.car_id).first()
        if not car:
            raise AppError("Car not found", 404)
        order.car_name = car.name
        order.car_cid = car.cid
        order.car_snapshot = _car_snapshot(car)

    if "user_id" in data:
        user = db.query(User).filter(User.id == order.user_id).first()
        if not user:
            raise AppError("User not found", 404)

    order.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(order)
    if "paid_amount" in data or "payment_method" in data or "date" in data:
        _sync_initial_payment(
            db,
            order,
            data.get("paid_amount", order.paid_amount),
            data.get("payment_method", order.payment_method),
            data.get("date", order.date),
        )
    recalc_orders_from_payments(db, order.id)
    sync_car_rankings(db, order.car_id)
    sync_user_totals(db, old_user_id)
    if order.user_id != old_user_id:
        sync_user_totals(db, order.user_id)
    return order


def update_order_status(db: Session, order: Order, status: OrderStatus) -> Order:
    order.status = status
    order.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(order)
    sync_user_totals(db, order.user_id)
    sync_car_rankings(db, order.car_id)
    return order


def delete_order(db: Session, order: Order) -> None:
    user_id = order.user_id
    car_id = order.car_id
    db.delete(order)
    db.commit()
    sync_user_totals(db, user_id)
    sync_car_rankings(db, car_id)


def sync_user_totals(db: Session, user_id: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    user.total_orders = len(orders)
    user.total_paid = sum(order.paid_amount for order in orders)
    user.total_balance = sum(order.balance_amount for order in orders)
    user.last_active = datetime.now(UTC)
    db.commit()


def recalc_orders_from_payments(db: Session, order_id: str) -> None:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return
    payments = db.query(Payment).filter(Payment.order_id == order_id).all()
    order.paid_amount = sum(payment.amount for payment in payments if payment.status == UserPaymentStatus.confirmed)
    _sync_payment_state(order)
    if order.car_snapshot is None:
        car = db.query(Car).filter(Car.id == order.car_id).first()
        if car:
            order.car_snapshot = _car_snapshot(car)
    db.commit()
    sync_user_totals(db, order.user_id)
    sync_car_rankings(db, order.car_id)


def list_order_payments(db: Session, order_id: str):
    return db.query(Payment).filter(Payment.order_id == order_id).order_by(Payment.date.desc()).all()
