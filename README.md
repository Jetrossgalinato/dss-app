# Enrollment Forecasting DSS

Offline Decision Support System for enrollment forecasting (Electron + Vue 3 +
FastAPI + embedded SQLite, with optional PostgreSQL development support).

## Install the desktop application

End-user installers are produced for:

- Windows x64: NSIS `.exe`
- Linux x64: AppImage and `.deb`

The installed application is self-contained and offline. It starts its bundled
FastAPI service automatically and stores enrollment data in a local SQLite
database; end users do not need Docker, PostgreSQL, Python, or Node.js.

The initial installers are unsigned, so Windows SmartScreen or Linux desktop
security may ask for confirmation. Code signing and automatic updates are not
configured.

The `.deb` package is preferred on Ubuntu/Debian systems because it configures
Electron's sandbox during installation. If an AppImage cannot start because
the distribution disables unprivileged user namespaces, enable that OS feature
or launch the AppImage with `--no-sandbox` only as a compatibility fallback.

Application data is retained separately from the installed program:

- Windows: `%APPDATA%\Enrollment Forecasting DSS\data\enrollment.sqlite3`
- Linux: `~/.config/Enrollment Forecasting DSS/data/enrollment.sqlite3`

Backend logs are stored in the adjacent `logs/backend.log`. Close the
application before copying `enrollment.sqlite3` as a backup. Normal upgrades
and uninstalling the program do not delete this data.

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

In development, Electron starts a SQLite-backed FastAPI process through `uv`.
To use a separately running PostgreSQL backend instead:

```bash
cd frontend
DSS_BACKEND_URL=http://127.0.0.1:8000 npm run dev
```

On Linux systems without usable GPU acceleration, run
`npm run dev:compat`.

The Electron window calls the backend through a secure preload bridge
(`contextIsolation` and renderer sandboxing on, `nodeIntegration` off). Each
managed backend launch uses a random localhost port and private API token.

## Build installers

Install all build dependencies once:

```bash
cd backend
uv sync --group dev --group desktop
cd ../frontend
npm install
```

Build the installer for the current operating system:

```bash
cd frontend
npm run dist:win
# or
npm run dist:linux
```

Artifacts are written to `frontend/release/`. A platform-native GitHub Actions
workflow in `.github/workflows/desktop-build.yml` runs tests and uploads the
Windows and Linux installers. Windows installers must be built on Windows and
Linux installers on Linux because the bundled scientific Python backend is
platform-specific.

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

## Class size and section planning

Module C converts fresh forecasts into section recommendations:

```text
recommended sections = ceil(predicted enrollment / maximum class size)
planned class size = ceil(predicted enrollment / recommended sections)
```

The default maximum class size is 25 and can be changed from 1–100:

```bash
curl -X POST http://127.0.0.1:8000/api/sections/recommendations \
  -H "Content-Type: application/json" \
  -d '{"horizon": 3, "max_class_size": 25, "class_levels": null}'
```

In the desktop app, select **Forecast & Sections**, choose the maximum size and
forecast horizon, then select **Generate plan**. The modal displays projected
enrollment, recommended sections, planned class size, and the forecast method
for every class level and future academic year.

## Reports dashboard

Module D adds a dedicated **Reports** route to the desktop navigation. Reports
are generated on demand from the current enrollment records; they are not
stored in the database.

Use the class-level filter to view one level or all levels, select a 1–5 year
forecast horizon, and adjust the maximum class size from 1–100. The dashboard
shows:

- latest enrollment, year-over-year change, next-year forecast, and required sections;
- a historical-versus-forecast enrollment trend;
- stacked Male/Female enrollment totals;
- projected enrollment and recommended sections; and
- exact historical and projected values in accessible tables.

The unified report endpoint can also be called directly:

```bash
curl -X POST http://127.0.0.1:8000/api/reports/dashboard \
  -H "Content-Type: application/json" \
  -d '{"horizon": 3, "max_class_size": 25, "class_levels": null}'
```

Run all automated checks with:

```bash
cd backend && uv run pytest -q
cd ../frontend && npm test
cd ../frontend && npm run typecheck
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
