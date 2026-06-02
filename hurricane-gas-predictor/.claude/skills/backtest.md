---
name: backtest
description: Walk-forward backtest the buy signal on historical gold-layer data with MLflow logging
---

## Backtest

Runs walk-forward cross-validation on historical gold-layer data and logs results to MLflow.

### Steps
1. Ensure gold features span at least 2 hurricane seasons of data
2. Run: `python -m src.ml.backtest`
3. Review AUC, precision, and recall per fold in the output
4. Check MLflow for the `walk-forward-backtest` run
5. Run `pytest` before marking complete

### Rules
- Use walk-forward (time-ordered) splits — never `ShuffleSplit` on time-series data
- Backtest results are logged to MLflow alongside training runs
- A mean AUC below 0.60 indicates insufficient feature signal — revisit feature engineering
