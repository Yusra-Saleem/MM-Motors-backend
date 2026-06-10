from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import AccountStatus, User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.response_aliases import with_response_aliases
from app.core.supabase import supabase_admin


def _normalize_sort(sort_by: str | None, sort_dir: str | None) -> tuple[str, str]:
    normalized_sort = (sort_by or "newest").lower()
    normalized_dir = (sort_dir or "desc").lower()
    mapping = {
        "newest": ("registration_date", "desc"),
        "oldest": ("registration_date", "asc"),
        "name_asc": ("name", "asc"),
        "name_desc": ("name", "desc"),
        "email_asc": ("email", "asc"),
        "email_desc": ("email", "desc"),
    }
    if normalized_sort in {"registration_date", "updated_at", "name", "email"}:
        return normalized_sort, "desc" if normalized_dir != "asc" else "asc"
    return mapping.get(normalized_sort, ("registration_date", "desc"))


def serialize_user(db: Session, user: User) -> dict:
    favorites_count = db.query(Favorite).filter(Favorite.user_id == user.id).count()
    return with_response_aliases({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "type": user.role,
        "status": user.status,
        "avatar": user.avatar,
        "address": user.address,
        "total_orders": user.total_orders,
        "total_paid": user.total_paid,
        "total_balance": user.total_balance,
        "registration_date": user.registration_date,
        "last_active": user.last_active,
        "favorites_count": favorites_count,
    })


def serialize_user_detail(db: Session, user: User) -> dict:
    orders = (
        db.query(Order)
        .options(selectinload(Order.car), selectinload(Order.payments))
        .filter(Order.user_id == user.id)
        .order_by(Order.date.desc())
        .all()
    )
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == user.id)
        .order_by(Payment.date.desc())
        .all()
    )
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    payload = serialize_user(db, user)
    total_spent = sum(order.paid_amount for order in orders)
    active_orders = sum(1 for order in orders if order.status not in {"completed", "cancelled"})
    payload["orders"] = [
        {
            "id": order.id,
            "car_id": order.car_id,
            "car_name": order.car_name,
            "car_cid": order.car_cid,
            "car": order.car_snapshot
            or (
                {
                    "id": order.car.id,
                    "cid": order.car.cid,
                    "chassis_number": order.car.chassis_number,
                    "make": order.car.make,
                    "name": order.car.name,
                    "package": order.car.package,
                    "year": order.car.year,
                    "import_year": order.car.import_year,
                    "price": order.car.price,
                    "status": order.car.status,
                    "mileage": order.car.mileage,
                    "transmission": order.car.transmission,
                    "fuel_type": order.car.fuel_type,
                    "body_type": order.car.body_type,
                    "drive_type": order.car.drive_type,
                    "exterior_color": order.car.exterior_color,
                    "grade": order.car.grade,
                    "engine_type": order.car.engine_type,
                    "description": order.car.description,
                    "features": order.car.features or [],
                    "images": order.car.images or [],
                    "thumbnail": order.car.thumbnail,
                    "specifications": order.car.specifications or {},
                    "featured_flag": order.car.featured_flag,
                    "priority_score": order.car.priority_score,
                    "engagement_score": order.car.engagement_score,
                    "created_at": order.car.created_at,
                    "updated_at": order.car.updated_at,
                }
                if order.car
                else None
            ),
            "total_amount": order.total_amount,
            "paid_amount": order.paid_amount,
            "balance_amount": order.balance_amount,
            "payment_status": order.payment_status,
            "status": order.status,
            "date": order.date,
            "payment_method": order.payment_method,
            "notes": order.notes,
            "payments": [
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
                for payment in order.payments
            ],
        }
        for order in orders
    ]
    payload["payments"] = [
        {
            "id": payment.id,
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
    payload["favorites"] = [
        {
            "id": favorite.id,
            "car_id": favorite.car_id,
            "created_at": favorite.created_at,
        }
        for favorite in favorites
    ]
    payload["summary"] = {
        "total_orders": len(orders),
        "total_spent": total_spent,
        "active_orders": active_orders,
    }
    return with_response_aliases(payload)


def create_user(db: Session, payload: UserCreate, actor: User | None = None) -> User:
    if payload.role == UserRole.admin:
        raise AppError("Cannot create admin users", 400)

    if db.query(User).filter(User.email == payload.email).first():
        raise AppError("Email already exists", 409)

    # 1. Create user in Supabase Auth
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

    # 2. Create profile in local Database
    user = User(
        id=supabase_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        status=payload.status,
        password_hash=hash_password(payload.password),
        avatar=payload.avatar,
        address=payload.address,
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


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    if data.get("role") == UserRole.admin:
        raise AppError("Cannot assign admin role", 400)

    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, new_password: str) -> User:
    # 1. Update in Supabase Auth
    try:
        supabase_admin.auth.admin.update_user_by_id(user.id, {"password": new_password})
    except Exception as exc:
        raise AppError(f"Failed to update password in auth service: {str(exc)}", 500)

    # 2. Update locally
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def set_user_status(db: Session, user: User, status: AccountStatus) -> User:
    user.status = status
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    # 1. Delete from Supabase Auth
    try:
        supabase_admin.auth.admin.delete_user(user.id)
    except Exception as exc:
        # We might want to log this but proceed with DB deletion if user is already gone from Supabase
        print(f"Warning: Failed to delete user from Supabase: {str(exc)}")

    # 2. Delete from local DB
    db.delete(user)
    db.commit()


def get_user_or_404(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role == UserRole.admin:
        raise AppError("User not found", 404)
    return user


def list_users(
    db: Session,
    page: int,
    page_size: int,
    query: str | None,
    role: UserRole | None,
    status: AccountStatus | None,
    sort_by: str,
    sort_dir: str,
):
    normalized_sort, normalized_dir = _normalize_sort(sort_by, sort_dir)
    qs = db.query(User).filter(User.role != UserRole.admin)
    if query:
        like = f"%{query}%"
        qs = qs.filter(
            or_(
                User.name.ilike(like),
                User.email.ilike(like),
                User.phone.ilike(like),
                User.address.ilike(like),
                cast(User.role, String).ilike(like),
            )
        )
    if role:
        qs = qs.filter(User.role == role)
    if status:
        qs = qs.filter(User.status == status)
    sort_column = getattr(User, normalized_sort, User.registration_date)
    qs = qs.order_by(sort_column.desc() if normalized_dir == "desc" else sort_column.asc())
    total = qs.order_by(None).count()
    items = qs.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [serialize_user(db, item) for item in items],
        "meta": {
            "page": page,
            "pageSize": page_size,
            "page_size": page_size,
            "total": total,
            "totalPages": max(1, -(-total // page_size)),
            "total_pages": max(1, -(-total // page_size)),
        },
    }


def list_user_orders(db: Session, user_id: str, page: int = 1, page_size: int = 100):
    qs = db.query(Order).filter(Order.user_id == user_id).order_by(Order.date.desc())
    total = qs.order_by(None).count()
    items = qs.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def list_user_payments(db: Session, user_id: str, page: int = 1, page_size: int = 100):
    qs = db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.date.desc())
    total = qs.order_by(None).count()
    items = qs.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
