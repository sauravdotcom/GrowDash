# Backend (FastAPI + PostgreSQL + Pandas)

## 1) Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` if needed.

## 2) Run API

```bash
uvicorn app.main:app --reload --reload-dir app --port 7000
```

## 3) Endpoints

- `POST /api/v1/trades/upload` -> upload Groww tradebook CSV (`multipart/form-data`, field name: `file`)
- `GET /api/v1/trades` -> list trades
- `GET /api/v1/analytics` -> full analytics payload
- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/daily-pnl`
- `GET /api/v1/analytics/monthly-pnl`
- `GET /api/v1/analytics/ce-vs-pe`
- `GET /api/v1/analytics/most-traded-strike`
- `GET /api/v1/analytics/holding-time`
- `POST /api/v1/ai/copilot` -> AI copilot response from your analytics data

Optional env vars:

- `OPENAI_API_KEY` (if not set, copilot runs in rule-based fallback mode)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
