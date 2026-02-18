from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.ai_copilot import generate_copilot_response
from app.services.analytics import get_trade_analytics


router = APIRouter(prefix="/ai", tags=["AI Copilot"])


@router.post("/copilot", response_model=CopilotResponse)
def copilot_advice(payload: CopilotRequest, db: Session = Depends(get_db)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    analytics = get_trade_analytics(db)

    try:
        return generate_copilot_response(question, analytics)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
