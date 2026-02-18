from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import (
    AnalyticsResponse,
    CePePoint,
    DailyPnlPoint,
    HoldingTimeAnalysis,
    MonthlyPnlPoint,
    StrikePoint,
    SummaryMetrics,
)
from app.services.analytics import get_trade_analytics


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse)
def analytics_overview(db: Session = Depends(get_db)):
    return get_trade_analytics(db)


@router.get("/summary", response_model=SummaryMetrics)
def analytics_summary(db: Session = Depends(get_db)):
    analytics = get_trade_analytics(db)
    return analytics["summary"]


@router.get("/daily-pnl", response_model=list[DailyPnlPoint])
def analytics_daily_pnl(db: Session = Depends(get_db)):
    analytics = get_trade_analytics(db)
    return analytics["daily_pnl"]


@router.get("/monthly-pnl", response_model=list[MonthlyPnlPoint])
def analytics_monthly_pnl(db: Session = Depends(get_db)):
    analytics = get_trade_analytics(db)
    return analytics["monthly_pnl"]


@router.get("/ce-vs-pe", response_model=list[CePePoint])
def analytics_ce_vs_pe(db: Session = Depends(get_db)):
    analytics = get_trade_analytics(db)
    return analytics["ce_vs_pe"]


@router.get("/most-traded-strike", response_model=list[StrikePoint])
def analytics_most_traded_strike(db: Session = Depends(get_db)):
    analytics = get_trade_analytics(db)
    return analytics["most_traded_strike"]


@router.get("/holding-time", response_model=HoldingTimeAnalysis)
def analytics_holding_time(db: Session = Depends(get_db)):
    analytics = get_trade_analytics(db)
    return analytics["holding_time"]
