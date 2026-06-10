from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class FavoriteToggle(BaseModel):
    car_id: str


class FavoriteRead(ORMModel):
    id: int
    user_id: str
    car_id: str
    created_at: datetime

