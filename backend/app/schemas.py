from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    total_rows: int
    imported_rows: int
    skipped_rows: int


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: Optional[str]
    symbol: str
    exchange: Optional[str]
    segment: Optional[str]
    side: str
    quantity: int
    price: float
    traded_at: datetime
    strike: Optional[float]
    option_type: Optional[str]
    expiry: Optional[date]


class DailyPnlPoint(BaseModel):
    date: str
    pnl: float


class MonthlyPnlPoint(BaseModel):
    month: str
    pnl: float


class CePePoint(BaseModel):
    option_type: str
    pnl: float


class StrikePoint(BaseModel):
    strike: str
    quantity: int


class HoldingTimeAnalysis(BaseModel):
    average_minutes: float
    median_minutes: float
    min_minutes: float
    max_minutes: float


class SummaryMetrics(BaseModel):
    total_profit_loss: float
    win_rate: float
    average_profit: float
    average_loss: float
    risk_reward_ratio: Optional[float]
    max_drawdown: float


class TradeStats(BaseModel):
    total_trades: int
    closed_lots: int


class AnalyticsResponse(BaseModel):
    summary: SummaryMetrics
    daily_pnl: list[DailyPnlPoint]
    monthly_pnl: list[MonthlyPnlPoint]
    ce_vs_pe: list[CePePoint]
    most_traded_strike: list[StrikePoint]
    holding_time: HoldingTimeAnalysis
    trade_stats: TradeStats


class CopilotRequest(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    provider: str
    model: Optional[str] = None
    answer: str
    action_items: list[str]
    risk_flags: list[str]
    disclaimer: str
