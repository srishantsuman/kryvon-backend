from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import date
from math import ceil

from app.db.session import get_db
from app.schemas.trade import TradeCreate, TradeUpdate, TradeResponse, TradeListResponse
from app.services import trade_service
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=TradeListResponse)
def list_trades(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    symbol: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    tag: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trades, total = trade_service.get_trades(
        db, current_user.id, page, page_size, symbol, date_from, date_to, tag
    )
    return TradeListResponse(
        trades=trades,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 1,
    )


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_trade(
    trade_in: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return trade_service.create_trade(db, current_user.id, trade_in)


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return trade_service.get_trade_by_id(db, trade_id, current_user.id)


@router.patch("/{trade_id}", response_model=TradeResponse)
def update_trade(
    trade_id: int,
    trade_in: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return trade_service.update_trade(db, trade_id, current_user.id, trade_in)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade_service.delete_trade(db, trade_id, current_user.id)
