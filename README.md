# GrowDash Trading Analytics Dashboard

Personal dashboard for analyzing Groww Tradebook CSV exports without logging in to Groww.

## Stack

- Backend: FastAPI + Pandas + SQLAlchemy
- Frontend: Next.js (React) + Recharts
- Database: PostgreSQL

## Project Structure

```text
GrowDash/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analytics.py
│   │   │   ├── ai.py
│   │   │   └── trades.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── services/
│   │   │   ├── analytics.py
│   │   │   ├── ai_copilot.py
│   │   │   └── csv_parser.py
│   │   ├── config.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── sql/
│   │   └── schema.sql
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── AiCopilotPanel.tsx
│   │   ├── ChartsPanel.tsx
│   │   ├── SummaryCards.tsx
│   │   └── UploadPanel.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── package.json
│   └── .env.local.example
├── docker-compose.yml
└── README.md
```

## Database Schema

Main table is `trades` (see `backend/sql/schema.sql`).

Fields include:

- Trade identifiers: `id`, `trade_hash`, `order_id`
- Instrument metadata: `symbol`, `exchange`, `segment`, `strike`, `option_type`, `expiry`
- Execution data: `side`, `quantity`, `price`, `traded_at`
- Raw source row: `raw_payload`
- Audit: `created_at`

## Backend Features

- Upload Groww tradebook CSV: `POST /api/v1/trades/upload`
- Parse trades via Pandas with flexible header matching
- Store parsed trades in PostgreSQL (`trade_hash` dedupe)
- Analytics APIs:
  - `GET /api/v1/analytics` (full payload)
  - `GET /api/v1/analytics/summary`
  - `GET /api/v1/analytics/daily-pnl`
  - `GET /api/v1/analytics/monthly-pnl`
  - `GET /api/v1/analytics/ce-vs-pe`
  - `GET /api/v1/analytics/most-traded-strike`
  - `GET /api/v1/analytics/holding-time`
  - `POST /api/v1/ai/copilot`

Metrics implemented:

- total profit/loss
- daily pnl
- monthly pnl
- win rate
- average profit
- average loss
- risk reward ratio
- max drawdown
- CE vs PE performance
- most traded strike
- holding time analysis

## Frontend Features

- CSV upload form
- KPI summary cards
- Daily PnL line chart
- Monthly PnL bar chart
- CE vs PE performance chart
- Most traded strike bar chart
- Holding-time stats
- AI Trading Copilot Q&A panel

## Run Locally

### 1) Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2) Run Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --reload-dir app --port 7000
```

### 3) Run Frontend

Open a second terminal:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend: `http://localhost:4000`
Backend docs: `http://localhost:7000/docs`
