from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Trade
from app.db.session import get_db
from app.schemas import TradeOut, UploadResponse
from app.services.csv_parser import parse_tradebook_csv


router = APIRouter(prefix="/trades", tags=["Trades"])


@router.post("/upload", response_model=UploadResponse)
async def upload_tradebook(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        file_bytes = await file.read()
        parsed_rows = parse_tradebook_csv(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse CSV: {exc}") from exc

    if not parsed_rows:
        return UploadResponse(total_rows=0, imported_rows=0, skipped_rows=0)

    try:
        stmt = insert(Trade).values(parsed_rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["trade_hash"])
        result = db.execute(stmt)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database insert failed: {exc}") from exc

    imported_rows = result.rowcount if result.rowcount is not None else 0
    skipped_rows = len(parsed_rows) - imported_rows

    return UploadResponse(
        total_rows=len(parsed_rows),
        imported_rows=imported_rows,
        skipped_rows=skipped_rows,
    )


@router.get("", response_model=list[TradeOut])
def list_trades(
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    capped_limit = max(1, min(limit, 1000))
    trades = (
        db.query(Trade)
        .order_by(Trade.traded_at.desc(), Trade.id.desc())
        .offset(offset)
        .limit(capped_limit)
        .all()
    )
    return trades
