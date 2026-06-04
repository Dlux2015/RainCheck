# Hurricane Gas Predictor

[![CI](https://github.com/Dlux2015/RainCheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Dlux2015/RainCheck/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open source ML app that predicts optimal gas buying windows during Atlantic hurricane events.

**Live demo:** [rain-check-b261.vercel.app](https://rain-check-b261.vercel.app)

---

## Overview

Hurricane Gas Predictor monitors active Atlantic storms and Gulf Coast gas prices, then uses an XGBoost model to generate **BUY** or **WAIT** signals — helping drivers and fleets decide when to fill up before a storm-driven price spike.

The model is trained on **30 years of historical data**: EIA Gulf Coast weekly gas prices back to 1994, and NOAA HURDAT2 Atlantic hurricane records back to 1851. A key feature is `refinery_capacity_at_risk_pct` — the fraction of Gulf Coast refinery capacity within 250 km of any active storm track point — computed via Haversine cross-join in PySpark.

## Architecture

```
   NHC RSS ─────────┐
   EIA API ──────────┤    ┌──────────────────────┐
   HURDAT2 (1851+) ──┤──► │     Bronze Layer      │  append-only Delta tables
                     │    │   (raw ingestion)      │  UC Volume on Databricks
                     │    └──────────┬─────────────┘
                     │               │  PySpark clean + deduplicate
                     │    ┌──────────▼─────────────┐
                     │    │     Silver Layer         │  validated, typed records
                     │    └──────────┬─────────────┘
                     │               │  feature engineering (week-aligned join,
                     │               │  Haversine refinery proximity)
                     │    ┌──────────▼─────────────┐
                     │    │      Gold Layer          │  ML-ready features + labels
                     │    └──────────┬─────────────┘
                     │               │  XGBoost (200 trees)
                     │    ┌──────────▼─────────────┐
                     │    │    Model (UC Volume)     │  saved to
                     │    │                          │  /Volumes/.../models/
                     │    │                          │  hurricane-gas-signal
                     │    └──────────┬─────────────┘
                     │               │  FastAPI
                     │    ┌──────────▼──────────────────────────────────┐
                     │    │      React UI                                 │
                     │    │  BuySignalCard · StormMap · PriceChart        │
                     └────│  MetricRow · WeatherBackground + city select  │
                          └─────────────────────────────────────────────┘
```

## How It Works

1. **Storm Watch** — GitHub Actions polls the NHC RSS feed every 6 hours during hurricane season (June–November). Active storms trigger the Databricks ETL and training jobs.
2. **Price Poll** — A second workflow runs every 30 minutes year-round, fetching the latest Gulf Coast gas prices from the EIA Open Data API and upserting to Supabase.
3. **Feature Engineering** — PySpark jobs promote data bronze → silver → gold, computing 7 features:
   - `max_wind_kt` — peak wind speed of the strongest active storm that week
   - `active_storm_count` — number of distinct active storms
   - `storm_centroid_lat / lon` — geographic centre of all active storms
   - `price_7d_avg` — 7-week rolling average price per grade and region
   - `price_pct_change` — week-over-week price change
   - `refinery_capacity_at_risk_pct` — fraction of Gulf Coast refinery capacity within 250 km of any storm track point (Haversine cross-join, 5 refineries × all track points)
4. **ML Training** — XGBoost classifier trained on 30 years of weekly data. Label: `price_pct_change > 3%`. Model saved directly to a UC Volume path (no model registry).
5. **ML Inference** — Confidence ≥ 65% → **BUY** signal. The live signal, probability, and threshold are persisted to Supabase after each inference.
6. **Dashboard** — React + Leaflet frontend shows the live signal with confidence bar and historical accuracy metrics (AUC, Precision, Recall from a 5-fold walk-forward backtest). A dynamic sky background reflects current Florida weather and time of day.
7. **Monthly Retraining** — A scheduled workflow retrains the model on the 1st of each month. A separate annual workflow checks NOAA for a newer HURDAT2 file and opens a PR if one is found.

## Data Sources

| Source | Data | License |
|--------|------|---------|
| NOAA / NHC RSS | Active storm tracks and wind speed (live) | Public domain |
| NOAA HURDAT2 | Atlantic hurricane database 1851–present (~100k track records) | Public domain |
| EIA Open Data API | Gulf Coast weekly gas prices by grade — ~30 years of history | Public domain (free key at eia.gov) |
| EIA (seed data) | Gulf Coast refinery locations and capacity (5 major refineries) | Public domain |
| Open-Meteo | Current weather and sunrise/sunset for any Florida city | Free, no API key |

## Stack

| Layer | Technology |
|-------|-----------|
| Processing | PySpark (Databricks Free Edition) |
| Storage | Delta Lake on Unity Catalog Volumes (`/Volumes/workspace/default/raincheck/`) |
| ML | XGBoost + scikit-learn |
| Model storage | UC Volume path (direct file save — no model registry required) |
| API | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + Recharts + Leaflet |
| Weather | Open-Meteo API (free, no key — browser-side only) |
| Database | Supabase (Postgres) |
| CI/CD | GitHub Actions (5 workflows) |

## ML Features

| Feature | Description |
|---------|-------------|
| `max_wind_kt` | Peak wind (knots) of the strongest active storm that week |
| `active_storm_count` | Number of distinct named storms active that week |
| `storm_centroid_lat` | Average latitude of all active storm track points |
| `storm_centroid_lon` | Average longitude of all active storm track points |
| `price_7d_avg` | 7-week rolling average price per grade/region |
| `price_pct_change` | Week-over-week price change as a fraction |
| `refinery_capacity_at_risk_pct` | Fraction of Gulf Coast refinery capacity within 250 km of any storm |

**Label:** `price_pct_change > 0.03` (prices rose more than 3% that week) → 1, else 0  
**BUY threshold:** model confidence ≥ 65%

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/signal/latest` | Most recent BUY/WAIT signal from Supabase |
| `GET` | `/signal/accuracy` | Latest backtest metrics (AUC, precision, recall) |
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
| `model_metrics` | Walk-forward backtest results (AUC, precision, recall per training run) |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `BuySignalCard` | Signal display with confidence bar, explanation, historical accuracy bars (AUC/Precision/Recall), and last-updated time |
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

## Databricks Setup (one time)

The following notebooks must be run once in order on Databricks to populate the Delta tables and train the initial model:

| Notebook | Purpose |
|----------|---------|
| `00_historical_backfill` | Ingest HURDAT2 (1851–present) + 30 years of EIA prices; rebuild gold features |
| `01_bronze_ingest` | Live NHC RSS + EIA polling (run by scheduled jobs after initial setup) |
| `02_silver_features` | Bronze → silver (clean, deduplicate) |
| `03_gold_training_data` | Silver → gold (feature engineering) |
| `04_train_xgboost` | Train XGBoost and save model to UC Volume |
| `05_backtest` | Walk-forward backtest; push accuracy metrics to Supabase |
| `06_push_to_supabase` | Write latest signal to Supabase |

Each notebook always pulls the latest code from GitHub at runtime (`git clone --depth=1`).

## Deployment

### Backend (Railway)

1. Create a new Railway project and connect the `Dlux2015/RainCheck` repo
2. Set **Root Directory** to `hurricane-gas-predictor`
3. Add environment variables from your `.env` file
4. Railway detects `railway.toml` and starts `uvicorn` automatically

### Frontend (Vercel)

1. Import `Dlux2015/RainCheck` in Vercel
2. Set **Root Directory** to `hurricane-gas-predictor/frontend`
3. Add build-time environment variable: `VITE_API_URL=https://your-api.railway.app` (no trailing slash)
4. Deploy — Vercel detects Vite via `frontend/vercel.json`

> **Note:** `VITE_API_URL` must include `https://` and have no trailing slash.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `EIA_API_KEY` | EIA Open Data API key — free at https://www.eia.gov/opendata/ |
| `DATABRICKS_HOST` | Databricks workspace URL (e.g. `https://dbc-xxxx.cloud.databricks.com`) |
| `DATABRICKS_TOKEN` | Databricks personal access token |
| `DATABRICKS_JOB_ID_ETL` | ETL job ID (bronze → silver → gold → Supabase push) |
| `DATABRICKS_JOB_ID_SIGNAL` | Training job ID |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon (publishable) key |
| `NHC_RSS_URL` | NHC Atlantic RSS feed (default: `https://www.nhc.noaa.gov/nhc_at1.xml`) |
| `HURDAT2_URL` | NOAA HURDAT2 file URL — updated annually by the `hurdat2-update` workflow |

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Every push | Run pytest |
| `storm-watch.yml` | Every 6h, June–November | Poll NHC; trigger ETL + train on active storms |
| `price-poll.yml` | Every 30 min, year-round | Fetch latest EIA prices → Supabase |
| `retrain.yml` | 1st of every month at 02:00 UTC | Retrain model on fresh data |
| `hurdat2-update.yml` | January 1 annually | Check NOAA for a newer HURDAT2 file; open PR if found |

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run `pytest` before committing
4. Open a pull request against `main`

All dependencies must be open source and available on PyPI or npm.

## License

MIT — see [LICENSE](LICENSE) for details.
