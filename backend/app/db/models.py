from sqlalchemy import JSON, Column, Date, DateTime, Float, Integer, String, func

from app.db.session import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_hash = Column(String(64), nullable=False, unique=True, index=True)
    order_id = Column(String(64), nullable=True, index=True)

    symbol = Column(String(128), nullable=False, index=True)
    exchange = Column(String(32), nullable=True)
    segment = Column(String(32), nullable=True)
    side = Column(String(8), nullable=False, index=True)

    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    traded_at = Column(DateTime(timezone=False), nullable=False, index=True)

    strike = Column(Float, nullable=True, index=True)
    option_type = Column(String(8), nullable=True, index=True)
    expiry = Column(Date, nullable=True, index=True)

    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
