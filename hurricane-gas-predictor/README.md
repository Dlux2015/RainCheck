# Hurricane Gas Predictor

[![CI](https://github.com/Dlux2015/RainCheck/actions/workflows/ci.yml/badge.svg)](https://github.com/Dlux2015/RainCheck/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open source ML app that predicts optimal gas buying windows during Atlantic hurricane events.

**Live demo:** _Deploy to Vercel + Railway — see [Deployment](#deployment) below._

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
                    ┌──────────▼──────────┐
                    │      React UI        │  BuySignalCard · StormMap · PriceChart
                    └─────────────────────┘
```

## How It Works

1. **Storm Watch** — GitHub Actions polls the NHC RSS feed every 6 hours during hurricane season (June–November). When an active storm is detected (filtering out the off-season placeholder), it triggers the Databricks ETL and training jobs.
2. **Price Poll** — A second workflow runs every 30 minutes year-round, fetching the latest Gulf Coast gas prices from the EIA Open Data API and upserting to Supabase.
3. **Feature Engineering** — PySpark jobs promote data bronze → silver → gold, building features including storm intensity, proximity to Gulf Coast refineries, and 7-day rolling price averages per fuel grade.
4. **ML Inference** — An XGBoost classifier outputs the probability that prices will spike >3% in the next window. Confidence ≥65% → **BUY** signal.
5. **Dashboard** — A React + Leaflet frontend displays the live signal with a confidence bar, the Gulf Coast storm map, and 2 years of weekly price history for all three fuel grades.
6. **Monthly Retraining** — A scheduled workflow retrains the model on the 1st of each month as new price history accumulates.

## Data Sources

| Source | Data | License |
|--------|------|---------|
| NOAA / NHC RSS | Storm tracks, wind speed | Public domain |
| EIA Open Data API | Gulf Coast gas prices by grade (regular, midgrade, premium) | Public domain (free key at eia.gov) |
| EIA (seed data) | Gulf Coast refinery locations and capacity | Public domain |

## Stack

| Layer | Technology |
|-------|-----------|
| Processing | PySpark (Databricks Free Edition) |
| Storage | Delta Lake on Unity Catalog Volumes |
| ML | XGBoost + scikit-learn |
| Experiment tracking | MLflow (Unity Catalog registry) |
| API | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + Recharts + Leaflet |
| Database | Supabase (Postgres) |
| CI/CD | GitHub Actions |

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

1. Create a new Railway project and connect the GitHub repo
2. Set **Root Directory** to `hurricane-gas-predictor`
3. Add environment variables from your `.env` file
4. Railway will detect `railway.toml` and start with `uvicorn`

### Frontend (Vercel)

1. Import the GitHub repo in Vercel
2. Set **Root Directory** to `hurricane-gas-predictor/frontend`
3. Add environment variable: `VITE_API_URL=https://your-api.railway.app`
4. Deploy — Vercel detects Vite automatically

## Environment Variables

| Variable | Description |
|----------|-------------|
| `EIA_API_KEY` | EIA Open Data API key — free at https://www.eia.gov/opendata/ |
| `DATABRICKS_HOST` | Databricks workspace URL |
| `DATABRICKS_TOKEN` | Databricks personal access token |
| `DATABRICKS_JOB_ID_ETL` | Job ID: `599987463964025` |
| `DATABRICKS_JOB_ID_SIGNAL` | Job ID: `804866658302765` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `NHC_RSS_URL` | NHC Atlantic RSS feed (default: https://www.nhc.noaa.gov/nhc_at1.xml) |

## GitHub Actions Secrets Required

All environment variables above must also be set as GitHub Actions secrets
for the automated price polling, storm watching, and monthly retraining workflows.

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run `pytest` before committing
4. Open a pull request against `main`

All dependencies must be open source and available on PyPI or npm.

## License

MIT — see [LICENSE](LICENSE) for details.
