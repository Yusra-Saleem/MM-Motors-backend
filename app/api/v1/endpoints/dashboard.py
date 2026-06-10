from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth import require_roles
from app.services.dashboard import get_dashboard_stats
from app.services.response_envelope import success_response

router = APIRouter()


@router.get("/stats", response_model=dict)
def dashboard_stats(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    return success_response(get_dashboard_stats(db).model_dump(), "Dashboard stats retrieved")
