import time
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.car import CarStatus
from app.models.user import User, UserRole
from app.schemas.car import CarCreate, CarStatusUpdate, CarUpdate
from app.services.auth import require_roles
from app.services.cars import create_car, delete_car, get_car_or_404, get_featured_cars, list_cars, serialize_car, serialize_car_detail, update_car, update_car_status, upload_car_images
from app.services.response_envelope import success_response

class SimpleCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        if key in self._cache:
            val, expiry = self._cache[key]
            if expiry is None or expiry > time.time():
                return val
            else:
                del self._cache[key]
        return None

    def set(self, key, val, ttl=300):
        expiry = time.time() + ttl if ttl else None
        self._cache[key] = (val, expiry)

    def clear(self):
        self._cache.clear()

db_cache = SimpleCache()

router = APIRouter()


@router.get("", response_model=dict)
def get_cars(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    query: str | None = Query(default=None, alias="search"),
    status: CarStatus | None = None,
    year: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str = Query(default="newest", alias="sortBy"),
    sort_dir: str = Query(default="desc", alias="sortDir", pattern="^(asc|desc)$"),
    body_type: str | None = None,
    fuel_type: str | None = None,
    drive_type: str | None = None,
    make: str | None = None,
    package: str | None = None,
    featured: bool | None = None,
    db: Session = Depends(get_db),
):
    effective_page_size = limit or page_size
    cache_key = f"cars:page={page}:limit={effective_page_size}:query={query}:status={status}:year={year}:min_price={min_price}:max_price={max_price}:sort_by={sort_by}:sort_dir={sort_dir}:body_type={body_type}:fuel_type={fuel_type}:drive_type={drive_type}:make={make}:package={package}:featured={featured}"
    cached_res = db_cache.get(cache_key)
    if cached_res is not None:
        return cached_res

    items, total = list_cars(db, page, effective_page_size, query, status, year, min_price, max_price, sort_by, sort_dir, body_type, fuel_type, drive_type, make, package, featured)
    res = success_response({
        "items": [serialize_car(item) for item in items],
        "meta": {
            "page": page,
            "pageSize": effective_page_size,
            "page_size": effective_page_size,
            "limit": effective_page_size,
            "total": total,
            "totalPages": max(1, -(-total // effective_page_size)),
            "total_pages": max(1, -(-total // effective_page_size)),
        },
    }, "Cars retrieved")
    db_cache.set(cache_key, res, ttl=300)
    return res


@router.get("/featured", response_model=dict)
def get_featured(
    limit: int = Query(default=8, ge=1, le=24),
    db: Session = Depends(get_db),
):
    cache_key = f"featured:limit={limit}"
    cached_res = db_cache.get(cache_key)
    if cached_res is not None:
        return cached_res

    items = get_featured_cars(db, limit)
    res = success_response(
        {
            "items": [serialize_car(item) for item in items],
            "meta": {
                "page": 1,
                "pageSize": limit,
                "page_size": limit,
                "limit": limit,
                "total": len(items),
                "totalPages": 1,
                "total_pages": 1,
            },
        },
        "Featured cars retrieved",
    )
    db_cache.set(cache_key, res, ttl=300)
    return res


@router.post("", response_model=dict)
def post_car(payload: CarCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    db_cache.clear()
    car = create_car(db, payload)
    return success_response(serialize_car(car), "Car created")


@router.get("/{car_id}", response_model=dict)
def get_car(car_id: str, db: Session = Depends(get_db)):
    cache_key = f"car:{car_id}"
    cached_res = db_cache.get(cache_key)
    if cached_res is not None:
        return cached_res

    car = get_car_or_404(db, car_id)
    res = success_response(serialize_car_detail(db, car), "Car retrieved")
    db_cache.set(cache_key, res, ttl=300)
    return res


@router.patch("/{car_id}", response_model=dict)
def patch_car(car_id: str, payload: CarUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    db_cache.clear()
    car = get_car_or_404(db, car_id)
    return success_response(serialize_car(update_car(db, car, payload)), "Car updated")


@router.patch("/{car_id}/status", response_model=dict)
def patch_car_status(car_id: str, payload: CarStatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    db_cache.clear()
    car = get_car_or_404(db, car_id)
    return success_response(serialize_car(update_car_status(db, car, payload.status)), "Car status updated")


@router.post("/{car_id}/images", response_model=dict)
def upload_images(car_id: str, files: list[UploadFile] = File(...), db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    db_cache.clear()
    car = get_car_or_404(db, car_id)
    return success_response(serialize_car(upload_car_images(db, car, files)), "Images uploaded")


@router.delete("/{car_id}", response_model=dict)
def remove_car(car_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    db_cache.clear()
    car = get_car_or_404(db, car_id)
    delete_car(db, car)
    return success_response(message="Car deleted")
