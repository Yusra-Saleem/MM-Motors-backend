from __future__ import annotations

from datetime import UTC, datetime
from math import ceil
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models.car import Car, CarStatus
from app.models.favorite import Favorite
from app.models.order import Order
from app.schemas.car import CarCreate, CarUpdate
from app.services.response_aliases import with_response_aliases
from app.services.storage import build_object_name, upload_file_to_supabase


def _normalize_sort(sort_by: str | None, sort_dir: str | None) -> tuple[str, str]:
    normalized_sort = (sort_by or "newest").lower()
    normalized_dir = (sort_dir or "desc").lower()
    if normalized_sort in {"created_at", "updated_at", "year", "price", "priority_score", "engagement_score"}:
        return normalized_sort, "desc" if normalized_dir != "asc" else "asc"
    mapping = {
        "newest": ("created_at", "desc"),
        "oldest": ("created_at", "asc"),
        "price_asc": ("price", "asc"),
        "price_desc": ("price", "desc"),
        "year_asc": ("year", "asc"),
        "year_desc": ("year", "desc"),
        "featured": ("priority_score", "desc"),
    }
    return mapping.get(normalized_sort, ("created_at", "desc"))


def _sort_clause(model, sort_by: str, sort_dir: str):
    column = getattr(model, sort_by, model.created_at)
    return column.desc() if sort_dir == "desc" else column.asc()


def _apply_car_filters(qs, query: str | None, status: CarStatus | None, body_type: str | None, fuel_type: str | None, year: int | None, drive_type: str | None, make: str | None, package: str | None, min_price: float | None, max_price: float | None, featured: bool | None, sort_by: str, sort_dir: str):
    if query:
        like = f"%{query}%"
        qs = qs.filter(
            or_(
                Car.name.ilike(like),
                Car.cid.ilike(like),
                Car.chassis_number.ilike(like),
                Car.package.ilike(like),
                Car.make.ilike(like),
                Car.grade.ilike(like),
                Car.description.ilike(like),
                cast(Car.features, String).ilike(like),
            )
        )
    if status:
        qs = qs.filter(Car.status == status)
    if body_type:
        qs = qs.filter(Car.body_type.ilike(body_type))
    if fuel_type:
        qs = qs.filter(Car.fuel_type.ilike(fuel_type))
    if year:
        qs = qs.filter(Car.year == year)
    if drive_type:
        qs = qs.filter(Car.drive_type.ilike(drive_type))
    if make:
        qs = qs.filter(Car.make.ilike(make))
    if package:
        qs = qs.filter(Car.package.ilike(package))
    if min_price is not None:
        qs = qs.filter(Car.price >= min_price)
    if max_price is not None:
        qs = qs.filter(Car.price <= max_price)
    if featured is True:
        qs = qs.filter((Car.featured_flag.is_(True)) | (Car.priority_score > 0))
    elif featured is False:
        qs = qs.filter((Car.featured_flag.is_(False)) & (Car.priority_score <= 0))

    sort_column = _sort_clause(Car, sort_by, sort_dir)
    return qs.order_by(sort_column)


def list_cars(
    db: Session,
    page: int,
    page_size: int,
    query: str | None,
    status: CarStatus | None,
    year: int | None,
    min_price: float | None,
    max_price: float | None,
    sort_by: str,
    sort_dir: str,
    body_type: str | None = None,
    fuel_type: str | None = None,
    drive_type: str | None = None,
    make: str | None = None,
    package: str | None = None,
    featured: bool | None = None,
):
    normalized_sort, normalized_dir = _normalize_sort(sort_by, sort_dir)
    qs = db.query(Car).filter(Car.deleted_at.is_(None))
    qs = _apply_car_filters(qs, query, status, body_type, fuel_type, year, drive_type, make, package, min_price, max_price, featured, normalized_sort, normalized_dir)
    total = qs.order_by(None).count()
    items = qs.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_car_or_404(db: Session, car_id: str) -> Car:
    car = db.query(Car).filter(((Car.id == car_id) | (Car.cid == car_id)) & Car.deleted_at.is_(None)).first()
    if not car:
        raise AppError("Car not found", 404)
    return car


def serialize_car(car: Car) -> dict:
    return with_response_aliases({
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
        "created_at": car.created_at,
        "updated_at": car.updated_at,
    })


def serialize_car_detail(db: Session, car: Car) -> dict:
    orders = (
        db.query(Order)
        .filter(Order.car_id == car.id)
        .order_by(Order.date.desc())
        .all()
    )
    payload = serialize_car(car)
    payload["orders"] = [
        {
            "id": order.id,
            "user_id": order.user_id,
            "customer_name": order.customer_name,
            "total_amount": order.total_amount,
            "paid_amount": order.paid_amount,
            "balance_amount": order.balance_amount,
            "payment_status": order.payment_status,
            "status": order.status,
            "date": order.date,
        }
        for order in orders
    ]
    return with_response_aliases(payload)


def create_car(db: Session, payload: CarCreate) -> Car:
    cid_val = payload.cid
    # If not provided, or not 8 digits long, or not numeric, or already exists, generate a unique sequential one
    if not cid_val or len(cid_val) != 8 or not cid_val.isdigit() or db.query(Car).filter(Car.cid == cid_val).first():
        results = db.query(Car.cid).all()
        max_val = 0
        for row in results:
            c_str = row[0]
            if c_str and c_str.isdigit():
                val = int(c_str)
                if val > max_val:
                    max_val = val
        next_val = max_val + 1
        cid_val = f"{next_val:08d}"

    car = Car(
        id=payload.id or f"car-{uuid4().hex[:10]}",
        cid=cid_val,
        chassis_number=payload.chassis_number or f"CH-{uuid4().hex[:10].upper()}",
        make=payload.make,
        name=payload.name,
        package=payload.package or "",
        year=payload.year if payload.year is not None else datetime.now().year,
        import_year=payload.import_year,
        price=payload.price,
        status=payload.status,
        mileage=payload.mileage or "",
        transmission=payload.transmission or "",
        fuel_type=payload.fuel_type or "",
        body_type=payload.body_type or "",
        drive_type=payload.drive_type or "",
        exterior_color=payload.exterior_color or "",
        grade=payload.grade or "",
        engine_type=payload.engine_type or "",
        description=payload.description or "",
        features=payload.features,
        images=payload.images,
        thumbnail=payload.thumbnail,
        specifications=payload.specifications,
        featured_flag=payload.featured_flag,
        priority_score=payload.priority_score or 0,
        engagement_score=payload.engagement_score or 0,
    )
    db.add(car)
    db.commit()
    db.refresh(car)
    sync_car_rankings(db, car.id)
    return car


def update_car(db: Session, car: Car, payload: CarUpdate) -> Car:
    data = payload.model_dump(exclude_unset=True)
    # Ensure CID can never be edited or changed via update
    data.pop("cid", None)
    for field, value in data.items():
        if value is None:
            if field == "chassis_number":
                value = f"CH-{uuid4().hex[:10].upper()}"
            elif field in ["package", "mileage", "transmission", "fuel_type", "body_type", "drive_type", "exterior_color", "grade", "engine_type", "description"]:
                value = ""
            elif field == "year":
                value = datetime.now().year
        setattr(car, field, value)
    if car.featured_flag or car.priority_score > 0:
        car.priority_score = max(car.priority_score, car.engagement_score)
    db.commit()
    db.refresh(car)
    sync_car_rankings(db, car.id)
    return car


def update_car_status(db: Session, car: Car, status: CarStatus) -> Car:
    car.status = status
    car.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(car)
    sync_car_rankings(db, car.id)
    return car


def delete_car(db: Session, car: Car) -> None:
    car.deleted_at = datetime.now(UTC)
    car.updated_at = datetime.now(UTC)
    db.commit()


def upload_car_images(db: Session, car: Car, files: list[UploadFile]) -> Car:
    if not files:
        raise AppError("No images provided", 400)

    uploaded_urls: list[str] = []
    for index, file in enumerate(files, start=1):
        object_name = build_object_name(
            f"cars/{car.id}",
            f"{index:02d}-{uuid4().hex}-{file.filename or 'image'}",
        )
        uploaded_urls.append(upload_file_to_supabase(file, object_name))

    car.images = list(car.images or []) + uploaded_urls
    if not car.thumbnail and uploaded_urls:
        car.thumbnail = uploaded_urls[0]
    db.commit()
    db.refresh(car)
    sync_car_rankings(db, car.id)
    return car


def get_featured_cars(db: Session, limit: int = 8):
    qs = (
        db.query(Car)
        .filter(Car.deleted_at.is_(None))
        .filter(Car.status == CarStatus.available)
        .order_by(Car.featured_flag.desc(), Car.priority_score.desc(), Car.engagement_score.desc(), Car.created_at.desc())
        .limit(limit)
        .all()
    )
    return qs


def sync_car_rankings(db: Session, car_id: str) -> None:
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        return

    favorites_count = db.query(Favorite).filter(Favorite.car_id == car_id).count()
    orders_count = db.query(Order).filter(Order.car_id == car_id).count()
    engagement_score = float(favorites_count * 2 + orders_count)
    car.engagement_score = engagement_score
    if car.featured_flag:
        car.priority_score = max(car.priority_score, engagement_score)
    else:
        car.priority_score = max(car.priority_score, engagement_score * 0.75)
    db.commit()
