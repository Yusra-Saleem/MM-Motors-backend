from pydantic import BaseModel, Field
from app.schemas.common import ORMModel

class HomepageStatBase(BaseModel):
    value: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1, max_length=100)
    icon: str = Field(default="Car", max_length=50)
    priority: int = Field(default=0)

class HomepageStatCreate(HomepageStatBase):
    pass

class HomepageStatUpdate(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=50)
    label: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=50)
    priority: int | None = Field(default=None)

class HomepageStatRead(HomepageStatBase, ORMModel):
    id: int
