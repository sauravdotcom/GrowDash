CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    trade_hash VARCHAR(64) NOT NULL UNIQUE,
    order_id VARCHAR(64),
    symbol VARCHAR(128) NOT NULL,
    exchange VARCHAR(32),
    segment VARCHAR(32),
    side VARCHAR(8) NOT NULL,
    quantity INTEGER NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    traded_at TIMESTAMP NOT NULL,
    strike DOUBLE PRECISION,
    option_type VARCHAR(8),
    expiry DATE,
    raw_payload JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_traded_at ON trades (traded_at);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);
CREATE INDEX IF NOT EXISTS idx_trades_option_type ON trades (option_type);
CREATE INDEX IF NOT EXISTS idx_trades_strike ON trades (strike);
