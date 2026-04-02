from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import DashboardResponse
from app.services import analytics_service
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stats = analytics_service.get_dashboard_stats(db, current_user.id)
    daily_pnl = analytics_service.get_daily_pnl(db, current_user.id)
    return DashboardResponse(stats=stats, daily_pnl=daily_pnl)
