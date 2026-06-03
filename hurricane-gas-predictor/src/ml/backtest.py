"""Walk-forward backtest of the buy signal on historical gold-layer data."""

import os

import mlflow
import pandas as pd
import numpy as np
import requests
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from dotenv import load_dotenv

load_dotenv()

# Required Supabase table (run once):
#   CREATE TABLE model_metrics (
#     id            bigint generated always as identity primary key,
#     created_at    timestamptz default now(),
#     run_id        text,
#     n_folds       int,
#     mean_auc      float,
#     mean_precision float,
#     mean_recall   float
#   );

GOLD_PATH = "/Volumes/workspace/default/raincheck/delta/gold/features"
FEATURE_COLS = [
    "max_wind_kt",
    "active_storm_count",
    "storm_centroid_lat",
    "storm_centroid_lon",
    "price_7d_avg",
    "price_pct_change",
    "refinery_capacity_at_risk_pct",
]
LABEL_COL = "label"
THRESHOLD = 0.65


def _push_metrics_to_supabase(run_id: str, n_folds: int, mean_auc: float, mean_precision: float, mean_recall: float) -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("SUPABASE_URL/KEY not set — skipping metrics persist")
        return
    resp = requests.post(
        f"{url}/rest/v1/model_metrics",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json={
            "run_id": run_id,
            "n_folds": n_folds,
            "mean_auc": round(mean_auc, 4),
            "mean_precision": round(mean_precision, 4),
            "mean_recall": round(mean_recall, 4),
        },
    )
    resp.raise_for_status()
    print(f"Backtest metrics persisted to Supabase (run_id={run_id})")


def run_backtest(n_splits: int = 5) -> pd.DataFrame:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("backtest").getOrCreate()
    df = (
        spark.read.format("delta").load(GOLD_PATH)
             .toPandas()
             .dropna(subset=FEATURE_COLS + [LABEL_COL])
             .sort_values("week")
             .reset_index(drop=True)
    )

    fold_size = len(df) // (n_splits + 1)
    results = []

    with mlflow.start_run(run_name="walk-forward-backtest") as run:
        mlflow.log_param("n_splits", n_splits)
        mlflow.log_param("threshold", THRESHOLD)

        for i in range(n_splits):
            train_end = fold_size * (i + 1)
            test_slice = df.iloc[train_end: train_end + fold_size]
            if len(test_slice) == 0 or test_slice[LABEL_COL].nunique() < 2:
                continue

            model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1)
            model.fit(df.iloc[:train_end][FEATURE_COLS].values, df.iloc[:train_end][LABEL_COL].values)
            probs = model.predict_proba(test_slice[FEATURE_COLS].values)[:, 1]
            preds = (probs >= THRESHOLD).astype(int)

            results.append({
                "fold": i,
                "auc": roc_auc_score(test_slice[LABEL_COL], probs),
                "precision": precision_score(test_slice[LABEL_COL], preds, zero_division=0),
                "recall": recall_score(test_slice[LABEL_COL], preds, zero_division=0),
            })

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            mean_auc       = results_df["auc"].mean()
            mean_precision = results_df["precision"].mean()
            mean_recall    = results_df["recall"].mean()
            mlflow.log_metrics({
                "backtest_mean_auc":       mean_auc,
                "backtest_mean_precision": mean_precision,
                "backtest_mean_recall":    mean_recall,
            })
            _push_metrics_to_supabase(
                run_id=run.info.run_id,
                n_folds=len(results),
                mean_auc=mean_auc,
                mean_precision=mean_precision,
                mean_recall=mean_recall,
            )
        print(f"Backtest run {run.info.run_id} — {len(results)} folds")
        print(results_df.to_string(index=False))

    return results_df


if __name__ == "__main__":
    run_backtest()
