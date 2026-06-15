import os
from datetime import UTC, datetime

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.car import Car, CarStatus
from app.models.favorite import Favorite
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment, UserPaymentStatus
from app.models.user import AccountStatus, User, UserRole
from app.models.homepage_stat import HomepageStat


def _now() -> datetime:
    return datetime.now(UTC)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _car_snapshot(car: dict[str, object]) -> dict[str, object]:
    return {
        "id": car["id"],
        "cid": car["cid"],
        "name": car["name"],
        "package": car["package"],
        "year": car["year"],
        "price": car["price"],
        "thumbnail": car.get("thumbnail"),
        "status": car["status"],
    }


def seed_database() -> None:
    db = SessionLocal()

    try:
        # =========================
        # EXISTING DATA FETCH
        # =========================
        existing_users = db.query(User).all()
        existing_user_ids = {u.id for u in existing_users}
        existing_user_emails = {u.email for u in existing_users}

        existing_car_ids = {row[0] for row in db.query(Car.id).all()}
        existing_order_ids = {row[0] for row in db.query(Order.id).all()}
        existing_payment_ids = {row[0] for row in db.query(Payment.id).all()}
        existing_favorites = {
            (row[0], row[1]) for row in db.query(Favorite.user_id, Favorite.car_id).all()
        }

        # =========================
        # USERS SEED LIST
        # =========================
        users = []

        # =========================
        # ADMIN UPSERT
        # =========================
        admin_email = os.getenv("MM_MOTORS_ADMIN_EMAIL")
        admin_password = os.getenv("MM_MOTORS_ADMIN_PASSWORD")
        admin_id = os.getenv("MM_MOTORS_ADMIN_ID", "admin-1")

        if admin_email and admin_password:
            existing_admin = db.query(User).filter(User.id == admin_id).first()

            if existing_admin:
                # UPDATE ADMIN
                existing_admin.email = admin_email
                existing_admin.name = os.getenv("MM_MOTORS_ADMIN_NAME", "MM Motors Admin")
                existing_admin.role = UserRole.admin
                existing_admin.phone = os.getenv("MM_MOTORS_ADMIN_PHONE", "+92 300 0000000")
                existing_admin.address = os.getenv("MM_MOTORS_ADMIN_ADDRESS", "Karachi, Pakistan")
                existing_admin.password_hash = hash_password(admin_password)
                existing_admin.last_active = _now()

            else:
                # INSERT ADMIN
                users.append({
                    "id": admin_id,
                    "name": os.getenv("MM_MOTORS_ADMIN_NAME", "MM Motors Admin"),
                    "email": admin_email,
                    "phone": os.getenv("MM_MOTORS_ADMIN_PHONE", "+92 300 0000000"),
                    "role": UserRole.admin,
                    "status": AccountStatus.active,
                    "password": admin_password,
                    "address": os.getenv("MM_MOTORS_ADMIN_ADDRESS", "Karachi, Pakistan"),
                    "total_orders": 0,
                    "total_paid": 0,
                    "total_balance": 0,
                    "registration_date": _now(),
                    "last_active": _now(),
                })

        # =========================
        # OTHER USERS
        # =========================
        users.extend([
            {
                "id": "u1",
                "name": "Ahmed Hassan",
                "email": "ahmed.h@example.com",
                "phone": "+971 50 123 4567",
                "role": UserRole.dealer,
                "status": AccountStatus.active,
                "password": "Dealer12345!",
                "address": "Sheikh Zayed Road, Dubai, UAE",
                "total_orders": 1,
                "total_paid": 7500000,
                "total_balance": 27500000,
                "registration_date": _dt("2023-10-15T10:00:00+00:00"),
                "last_active": _now(),
            },
            {
                "id": "u2",
                "name": "Sarah Khan",
                "email": "sarah.k@example.com",
                "phone": "+92 300 9876543",
                "role": UserRole.stock_buyer,
                "status": AccountStatus.active,
                "password": "Buyer12345!",
                "address": "DHA Phase 6, Karachi, Pakistan",
                "total_orders": 1,
                "total_paid": 52000000,
                "total_balance": 0,
                "registration_date": _dt("2024-01-20T14:30:00+00:00"),
                "last_active": _now(),
            },
            {
                "id": "u3",
                "name": "John Doe",
                "email": "john@dealership.com",
                "phone": "+44 20 7123 4567",
                "role": UserRole.dealer,
                "status": AccountStatus.inactive,
                "password": "Dealer12345!",
                "address": "Mayfair, London, UK",
                "total_orders": 0,
                "total_paid": 0,
                "total_balance": 0,
                "registration_date": _dt("2022-05-12T09:15:00+00:00"),
                "last_active": _now(),
            },
        ])

        # =========================
        # INSERT USERS (SAFE)
        # =========================
        user_rows = []

        for data in users:
            if data["email"] in existing_user_emails:
                continue

            user_rows.append(
                User(
                    id=data["id"],
                    name=data["name"],
                    email=data["email"],
                    phone=data["phone"],
                    role=data["role"],
                    status=data["status"],
                    password_hash=hash_password(data["password"]),
                    address=data["address"],
                    total_orders=data["total_orders"],
                    total_paid=data["total_paid"],
                    total_balance=data["total_balance"],
                    registration_date=data["registration_date"],
                    last_active=data["last_active"],
                )
            )

        # =========================
        # CARS (UNCHANGED LOGIC)
        # =========================
        cars = []  # (your full car list stays same)

        car_rows = []
        for data in cars:
            if data["id"] in existing_car_ids:
                continue

            car_rows.append(
                Car(
                    id=data["id"],
                    cid=data["cid"],
                    chassis_number=data["chassis_number"],
                    make=data["make"],
                    name=data["name"],
                    package=data["package"],
                    year=data["year"],
                    import_year=data["import_year"],
                    price=data["price"],
                    status=data["status"],
                    mileage=data["mileage"],
                    transmission=data["transmission"],
                    fuel_type=data["fuel_type"],
                    body_type=data["body_type"],
                    drive_type=data["drive_type"],
                    exterior_color=data["exterior_color"],
                    grade=data["grade"],
                    engine_type=data["engine_type"],
                    description=data["description"],
                    features=data["features"],
                    images=data["images"],
                    thumbnail=data["thumbnail"],
                    featured_flag=data["featured_flag"],
                    priority_score=data["priority_score"],
                    engagement_score=data["engagement_score"],
                )
            )

        # =========================
        # SEED HOMEPAGE STATS
        # =========================
        existing_stats_count = db.query(HomepageStat).count()
        if existing_stats_count == 0:
            initial_stats = [
                HomepageStat(value="500+", label="Total Sales Cars", icon="Car", priority=0),
                HomepageStat(value="150+", label="Total Available Cars", icon="Users", priority=1),
                HomepageStat(value="15+", label="Proven Expertise", icon="Award", priority=2),
                HomepageStat(value="99%", label="Satisfied Customer", icon="Globe", priority=3),
            ]
            db.add_all(initial_stats)

        # =========================
        # SAVE
        # =========================
        db.add_all(user_rows + car_rows)
        db.flush()

        db.commit()

    finally:
        db.close()