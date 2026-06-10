from datetime import datetime

from pydantic import BaseModel, Field

from app.models.car import CarStatus
from app.schemas.common import ORMModel


class CarBase(BaseModel):
    cid: str | None = Field(default=None, max_length=128)
    chassis_number: str | None = Field(default=None, max_length=128)
    make: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=2, max_length=200)
    package: str | None = Field(default="", max_length=200)
    year: int | None = Field(default=None, ge=1950, le=2100)
    import_year: int | None = Field(default=None, ge=1950, le=2100)
    price: float = Field(gt=0)
    status: CarStatus = CarStatus.available
    mileage: str | None = Field(default="", max_length=100)
    transmission: str | None = Field(default="", max_length=100)
    fuel_type: str | None = Field(default="", max_length=100)
    body_type: str | None = Field(default="", max_length=100)
    drive_type: str | None = Field(default="", max_length=100)
    exterior_color: str | None = Field(default="", max_length=100)
    grade: str | None = Field(default="", max_length=50)
    engine_type: str | None = Field(default="", max_length=100)
    description: str | None = Field(default="", max_length=4000)
    features: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    thumbnail: str | None = None
    specifications: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    featured_flag: bool = False
    priority_score: float = 0
    engagement_score: float = 0


class CarCreate(CarBase):
    id: str | None = Field(default=None, max_length=64)


class CarUpdate(BaseModel):
    cid: str | None = Field(default=None, max_length=128)
    chassis_number: str | None = Field(default=None, max_length=128)
    make: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=200)
    package: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1950, le=2100)
    import_year: int | None = Field(default=None, ge=1950, le=2100)
    price: float | None = Field(default=None, gt=0)
    status: CarStatus | None = None
    mileage: str | None = Field(default=None, max_length=100)
    transmission: str | None = Field(default=None, max_length=100)
    fuel_type: str | None = Field(default=None, max_length=100)
    body_type: str | None = Field(default=None, max_length=100)
    drive_type: str | None = Field(default=None, max_length=100)
    exterior_color: str | None = Field(default=None, max_length=100)
    grade: str | None = Field(default=None, max_length=50)
    engine_type: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    features: list[str] | None = None
    images: list[str] | None = None
    thumbnail: str | None = None
    specifications: dict[str, str | int | float | bool | None] | None = None
    featured_flag: bool | None = None
    priority_score: float | None = None
    engagement_score: float | None = None


class CarStatusUpdate(BaseModel):
    status: CarStatus


class CarRead(ORMModel):
    id: str
    cid: str
    chassis_number: str
    make: str | None = None
    name: str
    package: str
    year: int
    import_year: int | None = None
    price: float
    status: CarStatus
    mileage: str
    transmission: str
    fuel_type: str
    body_type: str
    drive_type: str
    exterior_color: str
    grade: str
    engine_type: str
    description: str
    features: list[str]
    images: list[str]
    thumbnail: str | None = None
    specifications: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    featured_flag: bool = False
    priority_score: float = 0
    engagement_score: float = 0
    created_at: datetime
    updated_at: datetime


class CarOrderSummary(ORMModel):
    id: str
    user_id: str
    customer_name: str
    total_amount: float
    paid_amount: float
    balance_amount: float
    payment_status: str
    status: str
    date: datetime


class CarDetailRead(CarRead):
    orders: list[CarOrderSummary] = Field(default_factory=list)
