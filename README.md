# Enrollment Forecasting DSS

Offline Decision Support System for enrollment forecasting (Electron + Vue 3 + FastAPI + PostgreSQL).

## Prerequisites

- Docker / Docker Compose
- Node.js 20+
- Python 3.12+ with [uv](https://github.com/astral-sh/uv)

## Quick start

### 1. PostgreSQL

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Apply database migrations after the first setup and whenever new migrations are pulled:

```bash
cd backend
uv run alembic upgrade head
```

### 3. Frontend (Electron)

```bash
cd frontend
npm install
npm run dev
```

> On some Linux setups Electron needs `--no-sandbox` / `--disable-gpu` (already included in the npm scripts). If the chrome-sandbox binary complains about permissions, those flags keep local development working.

The Electron window shows a status view that calls the backend `/health` endpoint via a secure preload bridge (`contextIsolation` on, `nodeIntegration` off).

## Enrollment CSV format

Module A accepts UTF-8 CSV files up to 5 MB:

```csv
academic_year,class_level,sex,enrollment_count
2024-2025,Nursery,Female,18
2024-2025,Nursery,Male,16
```

Academic years must be consecutive, sex must be `Male` or `Female`, and counts
must be non-negative integers. Re-importing the same academic year, class level,
and sex updates the existing count.

## Enrollment forecasting

Module B generates total enrollment forecasts per class level by summing the
Male and Female historical records. Forecasts are computed on demand and are
not stored.

```bash
curl -X POST http://127.0.0.1:8000/api/forecasts/generate \
  -H "Content-Type: application/json" \
  -d '{"horizon": 3, "class_levels": ["Nursery"]}'
```

The `horizon` accepts 1–5 future academic years and defaults to 3. Omit
`class_levels` to forecast every available level. A response contains
chart-ready historical and projected points:

```json
{
  "horizon": 3,
  "series": [
    {
      "class_level": "Nursery",
      "method": "linear_trend",
      "observations_used": 3,
      "history": [
        {"academic_year": "2023-2024", "enrollment_count": 34}
      ],
      "forecast": [
        {"academic_year": "2024-2025", "predicted_count": 37}
      ]
    }
  ],
  "skipped": []
}
```

Series with at least five contiguous years use ARIMA `(1,1,0)`. Shorter
series with at least two years, gapped series, and failed ARIMA fits use a
linear trend. Predictions are rounded to whole learners and cannot be negative.

Run backend verification with:

```bash
cd backend
uv run pytest -q
```

## Project layout

```text
dss-app/
├── docker-compose.yml      # local PostgreSQL
├── backend/                # FastAPI + SQLAlchemy + Alembic
│   └── app/
└── frontend/               # electron-vite (Vue 3 + TS + Tailwind)
    └── src/
        ├── main/           # Electron main process
        ├── preload/        # IPC / contextBridge
        └── renderer/       # Vue UI
```
