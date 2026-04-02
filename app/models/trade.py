from datetime import datetime, timezone, date as date_type
from decimal import Decimal
from sqlalchemy import String, Numeric, Date, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.session import Base


class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Core trade fields — match exactly what the frontend sends
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    trade_type: Mapped[TradeType] = mapped_column(Enum(TradeType), nullable=False)

    # PnL is calculated server-side and stored — never trust client-sent PnL
    pnl: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=4), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Tags stored as JSON array — e.g. ["FOMO", "overtrading"]
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="trades")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Trade id={self.id} symbol={self.symbol} pnl={self.pnl}>"
