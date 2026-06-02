---
name: train-model
description: Train XGBoost buy-signal model with MLflow tracking and register to Model Registry
---

## Train Model

Trains the XGBoost classifier on gold-layer features with full MLflow tracking.

### Steps
1. Ensure gold features exist at `dbfs:/delta/gold/features`
2. Run: `python -m src.ml.train`
3. Verify the MLflow experiment has logged params, metrics, and an artifact
4. Confirm model is registered as `hurricane-gas-signal` in the Model Registry
5. Run `pytest tests/test_predict.py` before marking complete

### Rules
- MLflow **must** log params and metrics before calling `mlflow.register_model()`
- Never hardcode hyperparameters — pass via `params` dict or config file
- Target AUC ≥ 0.70 before promoting to Production stage
