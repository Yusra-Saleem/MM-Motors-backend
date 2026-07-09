from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


class CarStatus(str, Enum):
    available = "available"
    upcoming = "upcoming"
    sold = "sold"
    pending = "pending"


class Car(Base, TimestampMixin):
    __tablename__ = "cars"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    cid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    chassis_number: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    make: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    package: Mapped[str] = mapped_column(String(200), nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    import_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    status: Mapped[CarStatus] = mapped_column(SAEnum(CarStatus, name="car_status"), index=True, nullable=False, default=CarStatus.available)
    mileage: Mapped[str] = mapped_column(String(100), nullable=False)
    transmission: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    body_type: Mapped[str] = mapped_column(String(100), nullable=False)
    drive_type: Mapped[str] = mapped_column(String(100), nullable=False)
    exterior_color: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    engine_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    features: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    images: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    specifications: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=False)
    featured_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    engagement_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    orders = relationship("Order", back_populates="car")
    favorites = relationship("Favorite", back_populates="car", cascade="all, delete-orphan")
