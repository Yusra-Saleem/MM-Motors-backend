from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    refunded = "refunded"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    car_id: Mapped[str] = mapped_column(ForeignKey("cars.id", ondelete="RESTRICT"), index=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    car_name: Mapped[str] = mapped_column(String(200), nullable=False)
    car_cid: Mapped[str] = mapped_column(String(128), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    balance_amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.unpaid)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.pending)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    car_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user = relationship("User", back_populates="orders")
    car = relationship("Car", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
