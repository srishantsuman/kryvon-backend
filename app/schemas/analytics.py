from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


# ── Dashboard ──────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_pnl: Decimal
    win_rate: float
    total_trades: int
    avg_risk_reward: float
    winning_trades: int
    losing_trades: int


class DailyPnLPoint(BaseModel):
    date: str
    pnl: Decimal
    trades: int
    cumulative_pnl: Decimal


class DashboardResponse(BaseModel):
    stats: DashboardStats
    daily_pnl: list[DailyPnLPoint]


# ── Calendar ───────────────────────────────────────────────
class CalendarDayStats(BaseModel):
    date: str
    pnl: Decimal
    trades: int
    wins: int
    losses: int
    win_rate: float


class CalendarResponse(BaseModel):
    days: list[CalendarDayStats]
    monthly_pnl: Decimal
    monthly_win_rate: float
    monthly_trades: int
    current_streak: int
    streak_type: Optional[str]  # "win" | "loss" | None


# ── Analytics ──────────────────────────────────────────────
class TagStat(BaseModel):
    tag: str
    count: int
    total_pnl: Decimal
    avg_pnl: Decimal


class SymbolStat(BaseModel):
    symbol: str
    total_pnl: Decimal
    win_rate: float
    trades: int


class HourlyStat(BaseModel):
    hour: str
    avg_pnl: Decimal
    trades: int


class PnLRange(BaseModel):
    range: str
    count: int


class AnalyticsResponse(BaseModel):
    tag_analysis: list[TagStat]
    symbol_performance: list[SymbolStat]
    hourly_performance: list[HourlyStat]
    pnl_distribution: list[PnLRange]
    insights: list[str]
