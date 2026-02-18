from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Trade


@dataclass
class OpenLot:
    quantity: int
    price: float
    opened_at: datetime


def _normalize_option_type(option_type: str | None, symbol: str) -> str:
    if option_type and option_type.upper() in {"CE", "PE"}:
        return option_type.upper()

    upper_symbol = symbol.upper()
    if upper_symbol.endswith("CE"):
        return "CE"
    if upper_symbol.endswith("PE"):
        return "PE"
    return "UNKNOWN"


def _instrument_key(trade: Trade, option_type: str, strike: float | None) -> tuple[str, str, str, str]:
    return (
        trade.symbol,
        f"{strike:.2f}" if strike is not None else "",
        option_type,
        trade.expiry.isoformat() if trade.expiry else "",
    )


def _build_empty_analytics() -> dict[str, Any]:
    return {
        "summary": {
            "total_profit_loss": 0.0,
            "win_rate": 0.0,
            "average_profit": 0.0,
            "average_loss": 0.0,
            "risk_reward_ratio": None,
            "max_drawdown": 0.0,
        },
        "daily_pnl": [],
        "monthly_pnl": [],
        "ce_vs_pe": [],
        "most_traded_strike": [],
        "holding_time": {
            "average_minutes": 0.0,
            "median_minutes": 0.0,
            "min_minutes": 0.0,
            "max_minutes": 0.0,
        },
        "trade_stats": {
            "total_trades": 0,
            "closed_lots": 0,
        },
    }


def calculate_trade_analytics(trades: list[Trade]) -> dict[str, Any]:
    if not trades:
        return _build_empty_analytics()

    ordered_trades = sorted(trades, key=lambda item: (item.traded_at, item.id))

    open_longs: dict[tuple[str, str, str, str], deque[OpenLot]] = defaultdict(deque)
    open_shorts: dict[tuple[str, str, str, str], deque[OpenLot]] = defaultdict(deque)
    closed_positions: list[dict[str, Any]] = []
    strike_quantity: dict[str, int] = defaultdict(int)

    for trade in ordered_trades:
        qty = int(trade.quantity)
        if qty <= 0:
            continue

        side = (trade.side or "").upper()
        if side not in {"BUY", "SELL"}:
            continue

        option_type = _normalize_option_type(trade.option_type, trade.symbol)
        strike = trade.strike
        strike_key = f"{strike:.2f}" if strike is not None else "UNKNOWN"
        strike_quantity[strike_key] += qty

        key = _instrument_key(trade, option_type, strike)
        price = float(trade.price)

        if side == "BUY":
            remaining = qty
            shorts = open_shorts[key]

            while remaining > 0 and shorts:
                open_lot = shorts[0]
                matched_qty = min(remaining, open_lot.quantity)
                pnl = (open_lot.price - price) * matched_qty
                holding_minutes = max(
                    0.0,
                    (trade.traded_at - open_lot.opened_at).total_seconds() / 60.0,
                )
                closed_positions.append(
                    {
                        "closed_at": trade.traded_at,
                        "pnl": pnl,
                        "option_type": option_type,
                        "strike": strike_key,
                        "holding_minutes": holding_minutes,
                    }
                )

                open_lot.quantity -= matched_qty
                remaining -= matched_qty
                if open_lot.quantity == 0:
                    shorts.popleft()

            if remaining > 0:
                open_longs[key].append(OpenLot(quantity=remaining, price=price, opened_at=trade.traded_at))

        elif side == "SELL":
            remaining = qty
            longs = open_longs[key]

            while remaining > 0 and longs:
                open_lot = longs[0]
                matched_qty = min(remaining, open_lot.quantity)
                pnl = (price - open_lot.price) * matched_qty
                holding_minutes = max(
                    0.0,
                    (trade.traded_at - open_lot.opened_at).total_seconds() / 60.0,
                )
                closed_positions.append(
                    {
                        "closed_at": trade.traded_at,
                        "pnl": pnl,
                        "option_type": option_type,
                        "strike": strike_key,
                        "holding_minutes": holding_minutes,
                    }
                )

                open_lot.quantity -= matched_qty
                remaining -= matched_qty
                if open_lot.quantity == 0:
                    longs.popleft()

            if remaining > 0:
                open_shorts[key].append(
                    OpenLot(quantity=remaining, price=price, opened_at=trade.traded_at)
                )

    daily_pnl: dict[str, float] = defaultdict(float)
    monthly_pnl: dict[str, float] = defaultdict(float)
    ce_vs_pe: dict[str, float] = defaultdict(float)
    holding_samples: list[float] = []

    total_pnl = 0.0
    wins: list[float] = []
    losses: list[float] = []

    for position in closed_positions:
        pnl = float(position["pnl"])
        closed_at: datetime = position["closed_at"]

        total_pnl += pnl
        daily_pnl[closed_at.date().isoformat()] += pnl
        monthly_pnl[closed_at.strftime("%Y-%m")] += pnl
        ce_vs_pe[position["option_type"]] += pnl

        if pnl > 0:
            wins.append(pnl)
        elif pnl < 0:
            losses.append(abs(pnl))

        holding_samples.append(float(position["holding_minutes"]))

    closed_positions_sorted = sorted(closed_positions, key=lambda item: item["closed_at"])
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for position in closed_positions_sorted:
        equity += float(position["pnl"])
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)

    total_closed = len(closed_positions)
    win_rate = (len(wins) / total_closed * 100.0) if total_closed else 0.0
    average_profit = (sum(wins) / len(wins)) if wins else 0.0
    average_loss = (sum(losses) / len(losses)) if losses else 0.0
    risk_reward_ratio = (
        (average_profit / average_loss) if average_loss > 0 else None
    )

    if holding_samples:
        average_holding = sum(holding_samples) / len(holding_samples)
        median_holding = median(holding_samples)
        min_holding = min(holding_samples)
        max_holding = max(holding_samples)
    else:
        average_holding = median_holding = min_holding = max_holding = 0.0

    most_traded_strike = [
        {"strike": strike, "quantity": quantity}
        for strike, quantity in sorted(
            strike_quantity.items(), key=lambda item: item[1], reverse=True
        )
        if strike != "UNKNOWN"
    ]

    return {
        "summary": {
            "total_profit_loss": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "average_profit": round(average_profit, 2),
            "average_loss": round(average_loss, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2)
            if risk_reward_ratio is not None
            else None,
            "max_drawdown": round(max_drawdown, 2),
        },
        "daily_pnl": [
            {"date": day, "pnl": round(value, 2)}
            for day, value in sorted(daily_pnl.items(), key=lambda item: item[0])
        ],
        "monthly_pnl": [
            {"month": month, "pnl": round(value, 2)}
            for month, value in sorted(monthly_pnl.items(), key=lambda item: item[0])
        ],
        "ce_vs_pe": [
            {"option_type": option, "pnl": round(value, 2)}
            for option, value in sorted(ce_vs_pe.items(), key=lambda item: item[0])
        ],
        "most_traded_strike": most_traded_strike[:10],
        "holding_time": {
            "average_minutes": round(average_holding, 2),
            "median_minutes": round(median_holding, 2),
            "min_minutes": round(min_holding, 2),
            "max_minutes": round(max_holding, 2),
        },
        "trade_stats": {
            "total_trades": len(ordered_trades),
            "closed_lots": total_closed,
        },
    }


def get_trade_analytics(db: Session) -> dict[str, Any]:
    trades = db.query(Trade).order_by(Trade.traded_at.asc(), Trade.id.asc()).all()
    return calculate_trade_analytics(trades)
