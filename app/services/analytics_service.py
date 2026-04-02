from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timezone

from app.models.trade import Trade


def get_dashboard_stats(db: Session, user_id: int) -> dict:
    """Single query to get all stat card values."""
    trades = db.query(Trade).filter(Trade.user_id == user_id).all()

    if not trades:
        return {
            "total_pnl": Decimal("0"),
            "win_rate": 0.0,
            "total_trades": 0,
            "avg_risk_reward": 0.0,
            "winning_trades": 0,
            "losing_trades": 0,
        }

    total_pnl = sum(t.pnl for t in trades)
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    win_rate = (len(wins) / len(trades)) * 100

    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else Decimal("0")
    avg_loss = abs(sum(t.pnl for t in losses) / len(losses)) if losses else Decimal("0")
    avg_rr = float(avg_win / avg_loss) if avg_loss > 0 else 0.0

    return {
        "total_pnl": total_pnl,
        "win_rate": round(win_rate, 2),
        "total_trades": len(trades),
        "avg_risk_reward": round(avg_rr, 2),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
    }


def get_daily_pnl(db: Session, user_id: int) -> list[dict]:
    """GROUP BY date — efficient aggregation query."""
    rows = (
        db.query(
            Trade.date,
            func.sum(Trade.pnl).label("pnl"),
            func.count(Trade.id).label("trades"),
        )
        .filter(Trade.user_id == user_id)
        .group_by(Trade.date)
        .order_by(Trade.date)
        .all()
    )

    cumulative = Decimal("0")
    result = []
    for row in rows:
        cumulative += row.pnl
        result.append({
            "date": str(row.date),
            "pnl": row.pnl,
            "trades": row.trades,
            "cumulative_pnl": cumulative,
        })
    return result


def get_calendar_data(db: Session, user_id: int, year: int, month: int) -> dict:
    """All calendar data for a given month in one pass."""
    trades = (
        db.query(Trade)
        .filter(
            Trade.user_id == user_id,
            extract("year", Trade.date) == year,
            extract("month", Trade.date) == month,
        )
        .all()
    )

    # Build day-level stats
    day_map: dict[str, dict] = {}
    for trade in trades:
        key = str(trade.date)
        if key not in day_map:
            day_map[key] = {"pnl": Decimal("0"), "trades": 0, "wins": 0, "losses": 0}
        day_map[key]["pnl"] += trade.pnl
        day_map[key]["trades"] += 1
        if trade.pnl > 0:
            day_map[key]["wins"] += 1
        else:
            day_map[key]["losses"] += 1

    days = [
        {
            "date": k,
            "pnl": v["pnl"],
            "trades": v["trades"],
            "wins": v["wins"],
            "losses": v["losses"],
            "win_rate": round((v["wins"] / v["trades"]) * 100, 1) if v["trades"] > 0 else 0.0,
        }
        for k, v in sorted(day_map.items())
    ]

    # Monthly totals
    monthly_pnl = sum(t.pnl for t in trades)
    monthly_wins = sum(1 for t in trades if t.pnl > 0)
    monthly_trades = len(trades)
    monthly_win_rate = round((monthly_wins / monthly_trades) * 100, 1) if monthly_trades > 0 else 0.0

    # Streak calculation — look at days with trades, ordered
    ordered_days = sorted(day_map.items())
    streak = 0
    streak_type = None
    for _, v in reversed(ordered_days):
        is_win = v["pnl"] > 0
        if streak_type is None:
            streak_type = "win" if is_win else "loss"
            streak = 1
        elif (streak_type == "win" and is_win) or (streak_type == "loss" and not is_win):
            streak += 1
        else:
            break

    return {
        "days": days,
        "monthly_pnl": monthly_pnl,
        "monthly_win_rate": monthly_win_rate,
        "monthly_trades": monthly_trades,
        "current_streak": streak,
        "streak_type": streak_type,
    }


def get_analytics(db: Session, user_id: int) -> dict:
    """All analytics charts data."""
    trades = db.query(Trade).filter(Trade.user_id == user_id).all()

    if not trades:
        return {
            "tag_analysis": [],
            "symbol_performance": [],
            "hourly_performance": [],
            "pnl_distribution": [],
            "insights": ["Add some trades to see analytics."],
        }

    # Tag analysis
    tag_map: dict[str, dict] = {}
    for trade in trades:
        for tag in trade.tags:
            if tag not in tag_map:
                tag_map[tag] = {"count": 0, "total_pnl": Decimal("0")}
            tag_map[tag]["count"] += 1
            tag_map[tag]["total_pnl"] += trade.pnl

    tag_analysis = [
        {
            "tag": k,
            "count": v["count"],
            "total_pnl": v["total_pnl"],
            "avg_pnl": round(v["total_pnl"] / v["count"], 2),
        }
        for k, v in sorted(tag_map.items(), key=lambda x: x[1]["count"], reverse=True)
    ]

    # Symbol performance
    sym_map: dict[str, dict] = {}
    for trade in trades:
        s = trade.symbol
        if s not in sym_map:
            sym_map[s] = {"total_pnl": Decimal("0"), "trades": 0, "wins": 0}
        sym_map[s]["total_pnl"] += trade.pnl
        sym_map[s]["trades"] += 1
        if trade.pnl > 0:
            sym_map[s]["wins"] += 1

    symbol_performance = sorted(
        [
            {
                "symbol": k,
                "total_pnl": v["total_pnl"],
                "win_rate": round((v["wins"] / v["trades"]) * 100, 1),
                "trades": v["trades"],
            }
            for k, v in sym_map.items()
        ],
        key=lambda x: x["total_pnl"],
        reverse=True,
    )[:10]

    # Hourly performance
    hour_map: dict[int, dict] = {}
    for trade in trades:
        h = trade.created_at.hour
        if h not in hour_map:
            hour_map[h] = {"total_pnl": Decimal("0"), "count": 0}
        hour_map[h]["total_pnl"] += trade.pnl
        hour_map[h]["count"] += 1

    hourly_performance = [
        {
            "hour": f"{h}:00",
            "avg_pnl": round(v["total_pnl"] / v["count"], 2),
            "trades": v["count"],
        }
        for h, v in sorted(hour_map.items())
    ]

    # PnL distribution buckets
    buckets = [
        ("< -$50", lambda p: p < -50),
        ("-$50 to -$20", lambda p: -50 <= p < -20),
        ("-$20 to $0", lambda p: -20 <= p < 0),
        ("$0 to $20", lambda p: 0 <= p < 20),
        ("$20 to $50", lambda p: 20 <= p < 50),
        ("> $50", lambda p: p >= 50),
    ]
    pnl_distribution = [
        {"range": label, "count": sum(1 for t in trades if fn(float(t.pnl)))}
        for label, fn in buckets
    ]

    # Auto-generated insights
    insights = []
    if tag_analysis:
        worst = tag_analysis[0]
        insights.append(
            f"Your most common behavior tag is '{worst['tag']}' "
            f"({worst['count']} trades, avg PnL ${float(worst['avg_pnl']):.2f})"
        )
    if symbol_performance:
        best = symbol_performance[0]
        insights.append(
            f"Best performing symbol: {best['symbol']} with ${float(best['total_pnl']):.2f} total PnL"
        )
    if trades:
        avg_pnl = sum(float(t.pnl) for t in trades) / len(trades)
        insights.append(
            f"{len(trades)} total trades with ${avg_pnl:.2f} average PnL per trade"
        )

    return {
        "tag_analysis": tag_analysis,
        "symbol_performance": symbol_performance,
        "hourly_performance": hourly_performance,
        "pnl_distribution": pnl_distribution,
        "insights": insights,
    }
