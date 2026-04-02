from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status
from datetime import date

from app.models.trade import Trade, TradeType
from app.schemas.trade import TradeCreate, TradeUpdate


def calculate_pnl(entry: Decimal, exit_: Decimal, qty: Decimal, trade_type: TradeType) -> Decimal:
    """
    PnL calculated server-side — never trust the client.
    BUY: profit when price goes up (exit - entry) * qty
    SELL/SHORT: profit when price goes down (entry - exit) * qty
    """
    if trade_type == TradeType.BUY:
        return (exit_ - entry) * qty
    else:
        return (entry - exit_) * qty


def get_trades(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 50,
    symbol: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    tag: str | None = None,
) -> tuple[list[Trade], int]:
    """Paginated trade list with optional filters."""
    query = db.query(Trade).filter(Trade.user_id == user_id)

    if symbol:
        query = query.filter(Trade.symbol == symbol.upper())
    if date_from:
        query = query.filter(Trade.date >= date_from)
    if date_to:
        query = query.filter(Trade.date <= date_to)
    if tag:
        # JSON contains query — works in PostgreSQL
        query = query.filter(Trade.tags.contains([tag]))

    total = query.count()
    trades = (
        query.order_by(Trade.date.desc(), Trade.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return trades, total


def get_trade_by_id(db: Session, trade_id: int, user_id: int) -> Trade:
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user_id).first()
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return trade


def create_trade(db: Session, user_id: int, trade_in: TradeCreate) -> Trade:
    pnl = calculate_pnl(trade_in.entry_price, trade_in.exit_price, trade_in.quantity, trade_in.trade_type)

    trade = Trade(
        user_id=user_id,
        date=trade_in.date,
        symbol=trade_in.symbol,
        entry_price=trade_in.entry_price,
        exit_price=trade_in.exit_price,
        quantity=trade_in.quantity,
        trade_type=trade_in.trade_type,
        pnl=pnl,
        notes=trade_in.notes,
        tags=trade_in.tags,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


def update_trade(db: Session, trade_id: int, user_id: int, trade_in: TradeUpdate) -> Trade:
    trade = get_trade_by_id(db, trade_id, user_id)

    update_data = trade_in.model_dump(exclude_unset=True)

    # If price/qty/type fields changed, recalculate PnL
    price_fields = {"entry_price", "exit_price", "quantity", "trade_type"}
    if price_fields & set(update_data.keys()):
        entry = update_data.get("entry_price", trade.entry_price)
        exit_ = update_data.get("exit_price", trade.exit_price)
        qty = update_data.get("quantity", trade.quantity)
        t_type = update_data.get("trade_type", trade.trade_type)
        update_data["pnl"] = calculate_pnl(Decimal(str(entry)), Decimal(str(exit_)), Decimal(str(qty)), t_type)

    for field, value in update_data.items():
        setattr(trade, field, value)

    db.commit()
    db.refresh(trade)
    return trade


def delete_trade(db: Session, trade_id: int, user_id: int) -> None:
    trade = get_trade_by_id(db, trade_id, user_id)
    db.delete(trade)
    db.commit()
