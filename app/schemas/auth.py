from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.stock_buyer
    address: str = Field(default="")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class MeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, min_length=6, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    avatar: str | None = None


from app.schemas.user import UserRead  # noqa: E402,F401
