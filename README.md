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

### 3. Frontend (Electron)

```bash
cd frontend
npm install
npm run dev
```

> On some Linux setups Electron needs `--no-sandbox` / `--disable-gpu` (already included in the npm scripts). If the chrome-sandbox binary complains about permissions, those flags keep local development working.

The Electron window shows a status view that calls the backend `/health` endpoint via a secure preload bridge (`contextIsolation` on, `nodeIntegration` off).

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
