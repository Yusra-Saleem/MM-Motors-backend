from sqlalchemy.orm import Session
from app.models.homepage_stat import HomepageStat
from app.schemas.homepage_stat import HomepageStatCreate, HomepageStatUpdate
from app.core.errors import AppError

def serialize_homepage_stat(stat: HomepageStat) -> dict:
    return {
        "id": stat.id,
        "value": stat.value,
        "label": stat.label,
        "icon": stat.icon,
        "priority": stat.priority,
    }

def list_homepage_stats(db: Session) -> list[HomepageStat]:
    return db.query(HomepageStat).order_by(HomepageStat.priority.asc(), HomepageStat.id.asc()).all()

def get_homepage_stat_or_404(db: Session, stat_id: int) -> HomepageStat:
    stat = db.query(HomepageStat).filter(HomepageStat.id == stat_id).first()
    if not stat:
        raise AppError("Homepage stat not found", 404)
    return stat

def create_homepage_stat(db: Session, payload: HomepageStatCreate) -> HomepageStat:
    stat = HomepageStat(
        value=payload.value,
        label=payload.label,
        icon=payload.icon,
        priority=payload.priority,
    )
    db.add(stat)
    db.commit()
    db.refresh(stat)
    return stat

def update_homepage_stat(db: Session, stat: HomepageStat, payload: HomepageStatUpdate) -> HomepageStat:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(stat, field, value)
    db.commit()
    db.refresh(stat)
    return stat

def delete_homepage_stat(db: Session, stat: HomepageStat) -> None:
    db.delete(stat)
    db.commit()
