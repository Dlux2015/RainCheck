# Hurricane Gas Predictor — Claude Code Rules

## Data Layer Rules
- **Bronze layer is append-only**: never overwrite existing records; always use Delta Lake `.mode("append")`
- Silver and gold layers may be overwritten on reprocessing
- All PySpark jobs write to Delta Lake using `.format("delta")`

## Security Rules
- **Never hardcode API keys**: always use `os.getenv()` or `python-dotenv`
- No credentials, tokens, or secrets in source files or notebooks
- `.env` is gitignored — copy from `.env.example`

## ML Rules
- **MLflow logs every training run before model registration**: call `mlflow.log_params()`, `mlflow.log_metrics()`, and `mlflow.log_model()` *before* calling `mlflow.register_model()`
- Every experiment run must be reproducible from logged params

## Testing Rules
- **Run `pytest` before marking any task done**
- Tests live in `/tests/`; follow the `test_*.py` naming convention

## Open Source Rules
- This is an **MIT-licensed open source project**
- No proprietary dependencies — all packages must be on PyPI or npm under open licenses
- No company-specific branding or internal tooling

## Stack

| Layer | Technology |
|-------|-----------|
| Processing | PySpark |
| Storage | Delta Lake |
| ML | XGBoost + scikit-learn |
| Experiment tracking | MLflow |
| API | FastAPI + Uvicorn |
| Frontend | React 18 + Vite |
| Database | Supabase (Postgres) |
| Platform | Databricks Free Edition |
| CI/CD | GitHub Actions |
