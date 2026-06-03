# Hurricane Gas Predictor

[![CI](https://github.com/Dlux2015/RainCheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Dlux2015/RainCheck/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open source ML app that predicts optimal gas buying windows during Atlantic hurricane events.

**Live demo:** [rain-check-theta.vercel.app](https://rain-check-theta.vercel.app)

---

## Overview

Hurricane Gas Predictor monitors active Atlantic storms and Gulf Coast gas prices, then uses an XGBoost model to generate **BUY** or **WAIT** signals — helping drivers and fleets decide when to fill up before a storm-driven price spike.

## Architecture

```
                    ┌─────────────────────┐
   NHC RSS ──────►  │     Bronze Layer     │  ← append-only Delta tables
   EIA API ───────►  │  (raw ingestion)     │    UC Volume on Databricks
                    └──────────┬──────────┘
                               │  PySpark clean + deduplicate
                    ┌──────────▼──────────┐
                    │     Silver Layer     │  validated, typed records
                    └──────────┬──────────┘
                               │  feature engineering (week-aligned join)
                    ┌──────────▼──────────┐
                    │      Gold Layer      │  ML-ready features + labels
                    └──────────┬──────────┘
                               │  XGBoost + MLflow (Unity Catalog)
                    ┌──────────▼──────────┐
                    │    Model Registry    │  workspace.default.hurricane-gas-signal
                    │                      │  @champion alias
                    └──────────┬──────────┘
                               │  FastAPI
                    ┌──────────▼──────────────────────────────────┐
                    │      React UI                                 │
                    │  BuySignalCard · StormMap · PriceChart        │
                    │  MetricRow · WeatherBackground + city select  │
                    └─────────────────────────────────────────────┘
```

## How It Works

1. **Storm Watch** — GitHub Actions polls the NHC RSS feed every 6 hours during hurricane season (June–November). When an active storm is detected (filtering out the off-season placeholder), it triggers the Databricks ETL and training jobs.
2. **Price Poll** — A second workflow runs every 30 minutes year-round, fetching the latest Gulf Coast gas prices from the EIA Open Data API and upserting to Supabase.
3. **Feature Engineering** — PySpark jobs promote data bronze → silver → gold, building features including storm intensity, proximity to Gulf Coast refineries, and 7-day rolling price averages per fuel grade.
4. **ML Inference** — An XGBoost classifier outputs the probability that prices will spike >3% in the next window. Confidence ≥65% → **BUY** signal.
5. **Dashboard** — A React + Leaflet frontend displays the live signal with a confidence bar, the Gulf Coast storm map, and 2 years of weekly price history for all three fuel grades (regular, midgrade, premium). A dynamic sky background reflects the current Florida weather and time of day, powered by Open-Meteo. Users can select any of 16 Florida cities from the weather chip.
6. **Monthly Retraining** — A scheduled workflow retrains the model on the 1st of each month as new price history accumulates.

## Data Sources

| Source | Data | License |
|--------|------|---------|
| NOAA / NHC RSS | Storm tracks, wind speed | Public domain |
| EIA Open Data API | Gulf Coast gas prices by grade (regular, midgrade, premium) — 2 years weekly history | Public domain (free key at eia.gov) |
| EIA (seed data) | Gulf Coast refinery locations and capacity (5 major refineries) | Public domain |
| Open-Meteo | Current weather and sunrise/sunset for any Florida city | Free, no API key |

## Stack

| Layer | Technology |
|-------|-----------|
| Processing | PySpark (Databricks Free Edition) |
| Storage | Delta Lake on Unity Catalog Volumes (`/Volumes/workspace/default/raincheck/`) |
| ML | XGBoost + scikit-learn |
| Experiment tracking | MLflow (Unity Catalog registry, `@champion` alias) |
| API | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + Recharts + Leaflet |
| Weather | Open-Meteo API (free, no key — browser-side only) |
| Database | Supabase (Postgres) |
| CI/CD | GitHub Actions (3 workflows) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/signal/latest` | Most recent BUY/WAIT signal from Supabase |
| `POST` | `/signal/` | On-demand prediction from posted feature values |
| `GET` | `/prices/history` | Weekly price time series (`?grade=regular&days=730`) |
| `GET` | `/prices/latest` | Most recent price for every grade |
| `GET` | `/storm/active` | All currently active Atlantic storms |
| `GET` | `/storm/{storm_id}/track` | Ordered track points for a storm |

## Supabase Tables

| Table | Purpose |
|-------|---------|
| `storms` | Current active storm snapshot (upserted each ETL run) |
| `storm_track` | Full advisory history — one row per NHC advisory |
| `storm_flags` | Boolean flag: is any storm currently active? |
| `gas_prices` | Weekly Gulf Coast prices by grade and period |
| `signals` | ML BUY/WAIT signals with probability and features |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `BuySignalCard` | Signal display with animated confidence bar, explanation, and last-updated time |
| `StormMap` | Leaflet map of the Gulf Coast showing active storm positions |
| `PriceChart` | 2-year weekly price history for regular, midgrade, and premium grades |
| `MetricRow` | Active storm count, max wind speed, latest regular price with date |
| `WeatherBackground` | Dynamic sky gradient (clear/cloudy/rain/storm × day/dawn/dusk/night) with stars, sun, moon, and rain animation |
| `WeatherChip` | Clickable chip showing current Florida city weather — opens a grouped dropdown of 16 cities |

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/Dlux2015/RainCheck.git
cd RainCheck/hurricane-gas-predictor

# 2. Install Python dependencies (Python 3.10+)
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env — fill in EIA_API_KEY, SUPABASE_URL, SUPABASE_KEY, DATABRICKS_*

# 4. Start the API
uvicorn src.api.main:app --reload --port 8000

# 5. Start the frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Deployment

### Backend (Railway)

1. Create a new Railway project and connect the `Dlux2015/RainCheck` repo
2. Set **Root Directory** to `hurricane-gas-predictor`
3. Add environment variables from your `.env` file (see table below)
4. Railway detects `railway.toml` and starts `uvicorn` automatically

### Frontend (Vercel)

1. Import `Dlux2015/RainCheck` in Vercel
2. Set **Root Directory** to `hurricane-gas-predictor/frontend`
3. Add build-time environment variable: `VITE_API_URL=https://your-api.railway.app` (no trailing slash)
4. Deploy — Vercel detects Vite via `frontend/vercel.json`

> **Note:** `VITE_API_URL` must include `https://` and have no trailing slash. Without it the frontend treats the Railway URL as a path on the Vercel domain.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `EIA_API_KEY` | EIA Open Data API key — free at https://www.eia.gov/opendata/ |
| `DATABRICKS_HOST` | Databricks workspace URL (e.g. `https://dbc-xxxx.cloud.databricks.com`) |
| `DATABRICKS_TOKEN` | Databricks personal access token |
| `DATABRICKS_JOB_ID_ETL` | ETL job ID (bronze → silver → gold → Supabase push) |
| `DATABRICKS_JOB_ID_SIGNAL` | Training job ID (XGBoost train + MLflow register) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon (publishable) key |
| `NHC_RSS_URL` | NHC Atlantic RSS feed (default: `https://www.nhc.noaa.gov/nhc_at1.xml`) |

## GitHub Actions Secrets Required

The same variables above must be set as GitHub repository secrets for the three automated workflows:

| Workflow | Trigger | Secrets used |
|----------|---------|--------------|
| `ci.yml` | Every push | _(none — runs pytest only)_ |
| `storm-watch.yml` | Every 6h, June–November | `NHC_RSS_URL`, `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_JOB_ID_ETL`, `DATABRICKS_JOB_ID_SIGNAL` |
| `price-poll.yml` | Every 30 min, year-round | `EIA_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` |
| `retrain.yml` | 1st of every month at 02:00 UTC | `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_JOB_ID_ETL`, `DATABRICKS_JOB_ID_SIGNAL` |

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run `pytest` before committing
4. Open a pull request against `main`

All dependencies must be open source and available on PyPI or npm.

## License

MIT — see [LICENSE](LICENSE) for details.
