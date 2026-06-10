from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.favorite import Favorite
from app.models.user import User
from app.services.cars import sync_car_rankings


def list_favorites(db: Session, user_id: str):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()


def toggle_favorite(db: Session, user: User, car_id: str) -> tuple[bool, Favorite | None]:
    existing = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.car_id == car_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        sync_car_rankings(db, car_id)
        return False, None

    favorite = Favorite(user_id=user.id, car_id=car_id, created_at=datetime.now(UTC))
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    sync_car_rankings(db, car_id)
    return True, favorite
