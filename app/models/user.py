from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin


class UserRole(str, Enum):
    admin = "admin"
    dealer = "dealer"
    stock_buyer = "stock_buyer"


class AccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.stock_buyer)
    status: Mapped[AccountStatus] = mapped_column(SAEnum(AccountStatus, name="account_status"), nullable=False, default=AccountStatus.active)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)

    address: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    total_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_paid: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    total_balance: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

