from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.favorite import FavoriteToggle
from app.services.auth import current_user_dependency
from app.services.favorites import list_favorites, toggle_favorite
from app.services.response_aliases import with_response_aliases
from app.services.response_envelope import success_response

router = APIRouter()


@router.get("", response_model=dict)
def get_my_favorites(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="pageSize"),
    limit: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(current_user_dependency),
):
    effective_page_size = limit or page_size
    all_items = list_favorites(db, current_user.id)
    total = len(all_items)
    items = all_items[(page - 1) * effective_page_size : page * effective_page_size]
    return success_response({
        "items": [
            with_response_aliases(
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "car_id": item.car_id,
                    "created_at": item.created_at,
                }
            )
            for item in items
        ],
        "meta": {
            "page": page,
            "pageSize": effective_page_size,
            "page_size": effective_page_size,
            "limit": effective_page_size,
            "total": total,
            "totalPages": max(1, -(-total // effective_page_size)),
            "total_pages": max(1, -(-total // effective_page_size)),
        },
    }, "Favorites retrieved")


@router.post("/toggle", response_model=dict)
def toggle(payload: FavoriteToggle, db: Session = Depends(get_db), current_user: User = Depends(current_user_dependency)):
    added, favorite = toggle_favorite(db, current_user, payload.car_id)
    return success_response({
        "favorite": with_response_aliases(
            {
                "id": favorite.id,
                "user_id": favorite.user_id,
                "car_id": favorite.car_id,
                "created_at": favorite.created_at,
            }
        )
        if favorite
        else None,
        "result": "added" if added else "removed",
    }, "Favorite updated")
