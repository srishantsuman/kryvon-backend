from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.schemas.analytics import AnalyticsResponse, CalendarResponse
from app.services import analytics_service
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = analytics_service.get_analytics(db, current_user.id)
    return AnalyticsResponse(**data)


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month
    data = analytics_service.get_calendar_data(db, current_user.id, year, month)
    return CalendarResponse(**data)
