from datetime import datetime

from pydantic import BaseModel, Field

from app.models.order import OrderStatus, PaymentStatus
from app.schemas.car import CarRead
from app.schemas.common import ORMModel
from app.schemas.user import UserRead


class OrderBase(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    car_id: str = Field(min_length=1, max_length=64)
    customer_name: str = Field(min_length=2, max_length=200)
    total_amount: float = Field(gt=0)
    paid_amount: float = Field(default=0, ge=0)
    payment_status: PaymentStatus = PaymentStatus.unpaid
    status: OrderStatus = OrderStatus.pending
    date: datetime
    payment_method: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)
    car_snapshot: dict | None = None


class OrderCreate(OrderBase):
    id: str | None = Field(default=None, max_length=64)


class OrderUpdate(BaseModel):
    user_id: str | None = Field(default=None, max_length=64)
    car_id: str | None = Field(default=None, max_length=64)
    customer_name: str | None = Field(default=None, max_length=200)
    total_amount: float | None = Field(default=None, gt=0)
    paid_amount: float | None = Field(default=None, ge=0)
    payment_status: PaymentStatus | None = None
    status: OrderStatus | None = None
    date: datetime | None = None
    payment_method: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)
    car_snapshot: dict | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderRead(ORMModel):
    id: str
    user_id: str
    customer_name: str
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
    car_snapshot: dict | None = None


class OrderDetailRead(OrderRead):
    user: UserRead | None = None
    car: CarRead | None = None
    payments: list["OrderPaymentSummary"] = Field(default_factory=list)


class OrderPaymentSummary(ORMModel):
    id: str
    user_id: str
    order_id: str
    amount: float
    date: datetime
    method: str
    status: str
    notes: str | None = None
    transaction_metadata: dict | None = None


OrderDetailRead.model_rebuild()
