from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


class UserPaymentStatus(str, Enum):
    confirmed = "confirmed"
    pending = "pending"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[UserPaymentStatus] = mapped_column(SAEnum(UserPaymentStatus, name="user_payment_status"), nullable=False, default=UserPaymentStatus.pending)
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    transaction_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")
