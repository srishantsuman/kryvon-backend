from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from app.models.trade import TradeType


class TradeCreate(BaseModel):
    date: date
    symbol: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    trade_type: TradeType
    notes: Optional[str] = None
    tags: list[str] = []

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("quantity", "entry_price", "exit_price")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v

    @field_validator("tags")
    @classmethod
    def limit_tags(cls, v: list) -> list:
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [t.strip().lower() for t in v]


class TradeUpdate(BaseModel):
    date: Optional[date] = None
    symbol: Optional[str] = None
    entry_price: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    trade_type: Optional[TradeType] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v


class TradeResponse(BaseModel):
    id: int
    date: date
    symbol: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    trade_type: TradeType
    pnl: Decimal
    notes: Optional[str]
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    trades: list[TradeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
