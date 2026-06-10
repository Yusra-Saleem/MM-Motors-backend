from datetime import datetime

from pydantic import BaseModel, Field

from app.models.payment import UserPaymentStatus
from app.schemas.common import ORMModel


class PaymentBase(BaseModel):
    user_id: str | None = Field(default=None, min_length=1, max_length=64)
    order_id: str = Field(min_length=1, max_length=64)
    amount: float = Field(gt=0)
    date: datetime
    method: str = Field(min_length=1, max_length=100)
    status: UserPaymentStatus = UserPaymentStatus.pending
    notes: str | None = Field(default=None, max_length=4000)
    transaction_metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class PaymentCreate(PaymentBase):
    id: str | None = Field(default=None, max_length=64)


class PaymentUpdate(BaseModel):
    user_id: str | None = Field(default=None, max_length=64)
    order_id: str | None = Field(default=None, max_length=64)
    amount: float | None = Field(default=None, gt=0)
    date: datetime | None = None
    method: str | None = Field(default=None, max_length=100)
    status: UserPaymentStatus | None = None
    notes: str | None = Field(default=None, max_length=4000)
    transaction_metadata: dict[str, str | int | float | bool | None] | None = None


class PaymentRead(ORMModel):
    id: str
    user_id: str
    order_id: str
    amount: float
    date: datetime
    method: str
    status: UserPaymentStatus
    notes: str | None = None
    transaction_metadata: dict[str, str | int | float | bool | None] | None = None


class PaymentUserSummary(ORMModel):
    id: str
    name: str
    email: str


class PaymentOrderSummary(ORMModel):
    id: str
    user_id: str
    car_id: str
    car_name: str
    car_cid: str
    total_amount: float
    paid_amount: float
    balance_amount: float
    payment_status: str
    status: str
    date: datetime


class PaymentDetailRead(PaymentRead):
    user: PaymentUserSummary | None = None
    order: PaymentOrderSummary | None = None
