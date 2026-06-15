from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth import require_roles
from app.schemas.homepage_stat import HomepageStatCreate, HomepageStatUpdate
from app.services.homepage_stats import (
    list_homepage_stats,
    create_homepage_stat,
    get_homepage_stat_or_404,
    update_homepage_stat,
    delete_homepage_stat,
    serialize_homepage_stat,
)
from app.services.response_envelope import success_response

router = APIRouter()

@router.get("")
def get_stats(db: Session = Depends(get_db)):
    items = list_homepage_stats(db)
    serialized_items = [serialize_homepage_stat(item) for item in items]
    return success_response(serialized_items, "Homepage stats retrieved")

@router.post("")
def create_stat(
    payload: HomepageStatCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    item = create_homepage_stat(db, payload)
    return success_response(serialize_homepage_stat(item), "Homepage stat created")

@router.patch("/{stat_id}")
def update_stat(
    stat_id: int,
    payload: HomepageStatUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    item = get_homepage_stat_or_404(db, stat_id)
    updated_item = update_homepage_stat(db, item, payload)
    return success_response(serialize_homepage_stat(updated_item), "Homepage stat updated")

@router.delete("/{stat_id}")
def delete_stat(
    stat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    item = get_homepage_stat_or_404(db, stat_id)
    delete_homepage_stat(db, item)
    return success_response(None, "Homepage stat deleted")
