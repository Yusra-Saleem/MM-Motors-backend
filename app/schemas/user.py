from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import AccountStatus, UserRole
from app.models.order import OrderStatus, PaymentStatus
from app.models.payment import UserPaymentStatus
from app.schemas.common import ORMModel


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=50)
    role: UserRole = UserRole.stock_buyer
    status: AccountStatus = AccountStatus.active
    avatar: str | None = None
    address: str = Field(default="", max_length=500)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=6, max_length=50)
    status: AccountStatus | None = None
    avatar: str | None = None
    address: str | None = Field(default=None, max_length=500)
    role: UserRole | None = None


class UserPasswordUpdate(BaseModel):
    password: str


class UserStatusUpdate(BaseModel):
    status: AccountStatus


class UserRead(ORMModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    role: UserRole
    status: AccountStatus
    avatar: str | None = None
    address: str
    total_orders: int
    total_paid: float
    total_balance: float
    registration_date: datetime
    last_active: datetime
    favorites_count: int | None = 0


class UserFavoriteSummary(ORMModel):
    id: int
    car_id: str
    created_at: datetime


class UserPaymentSummary(ORMModel):
    id: str
    order_id: str
    amount: float
    date: datetime
    method: str
    status: UserPaymentStatus
    notes: str | None = None
    transaction_metadata: dict | None = None


class UserOrderSummary(ORMModel):
    id: str
    car_id: str
    car_name: str
    car_cid: str
    total_amount: float
    paid_amount: float
    balance_amount: float
    payment_status: PaymentStatus
    status: OrderStatus
    date: datetime
    payment_method: str
    notes: str | None = None


class UserDetailRead(UserRead):
    orders: list[UserOrderSummary] = Field(default_factory=list)
    payments: list[UserPaymentSummary] = Field(default_factory=list)
    favorites: list[UserFavoriteSummary] = Field(default_factory=list)
