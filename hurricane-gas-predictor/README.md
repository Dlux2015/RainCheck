# Hurricane Gas Predictor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open source ML app that predicts optimal gas buying windows during Atlantic hurricane events.

## Overview

Hurricane Gas Predictor monitors active Atlantic storms and Gulf Coast gas prices, then uses an XGBoost model to generate **BUY** or **WAIT** signals — helping drivers and fleets decide when to fill up before a storm-driven price spike.

## Architecture

```
                    ┌─────────────────────┐
   NHC RSS ──────►  │     Bronze Layer     │  ← append-only Delta tables
   Zyla API ─────►  │  (raw ingestion)     │
   EIA Data ─────►  └──────────┬──────────┘
                               │  PySpark clean + deduplicate
                    ┌──────────▼──────────┐
                    │     Silver Layer     │  validated, typed records
                    └──────────┬──────────┘
                               │  feature engineering + geo intersection
                    ┌──────────▼──────────┐
                    │      Gold Layer      │  ML-ready features + labels
                    └──────────┬──────────┘
                               │  XGBoost + MLflow
                    ┌──────────▼──────────┐
                    │    Model Registry    │  hurricane-gas-signal (MLflow)
                    └──────────┬──────────┘
                               │  FastAPI
                    ┌──────────▼──────────┐
                    │      React UI        │  BuySignalCard · StormMap
                    └─────────────────────┘
```

<!-- TODO: replace with a rendered architecture diagram (draw.io / Excalidraw) -->

## How It Works

1. **Storm Watch** — GitHub Actions polls the NHC RSS feed every 6 hours during hurricane season (June–November). When an active storm is detected, it triggers the Databricks ETL job.
2. **Price Poll** — A second workflow runs every 30 minutes, checks a Supabase storm-active flag, and fetches current Gulf Coast gas prices from the Zyla API.
3. **Feature Engineering** — PySpark jobs promote data bronze → silver → gold, building features including storm intensity, proximity to Gulf Coast refineries, and 7-day rolling price averages.
4. **ML Inference** — An XGBoost classifier outputs the probability that prices will spike >3% in the next window. Confidence ≥65% → **BUY** signal.
5. **Dashboard** — A React + Leaflet frontend displays the live signal, storm tracks on a map, and a 14-day price history chart.

## Data Sources

| Source | Data | License |
|--------|------|---------|
| NOAA / NHC RSS | Storm tracks, wind speed | Public domain |
| EIA (seed data) | Gulf Coast refinery locations | Public domain |
| Zyla API | US gas prices by region | Commercial (key required) |
| Supabase | Signal and price persistence | Open source / hosted |

## Stack

| Layer | Technology |
|-------|-----------|
| Processing | PySpark |
| Storage | Delta Lake |
| ML | XGBoost + scikit-learn |
| Experiment tracking | MLflow |
| API | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + Recharts + Leaflet |
| Database | Supabase (Postgres) |
| Platform | Databricks Free Edition |
| CI/CD | GitHub Actions |

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/Dlux2015/hurricane-gas-predictor.git
cd hurricane-gas-predictor

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your API keys

# 5. Start the API
uvicorn src.api.main:app --reload --port 8000

# 6. Start the frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ZYLA_API_KEY` | Zyla API key for US gas prices |
| `DATABRICKS_HOST` | Your Databricks workspace URL |
| `DATABRICKS_TOKEN` | Databricks personal access token |
| `DATABRICKS_JOB_ID_ETL` | Job ID for the ingestion/ETL Databricks job |
| `DATABRICKS_JOB_ID_SIGNAL` | Job ID for the signal generation job |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase anon or service role key |
| `NHC_RSS_URL` | NHC Atlantic RSS feed URL |

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run `pytest` before committing
4. Open a pull request against `main`

All dependencies must be open source and available on PyPI or npm.

## License

MIT — see [LICENSE](LICENSE) for details.
