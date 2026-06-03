"""Walk-forward backtest of the buy signal on historical gold-layer data."""

import mlflow
import pandas as pd
import numpy as np
import xgboost as xgb
from pyspark.sql import SparkSession
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from dotenv import load_dotenv

load_dotenv()

GOLD_PATH = "file:///tmp/delta/gold/features"
FEATURE_COLS = [
    "max_wind_kt",
    "active_storm_count",
    "storm_centroid_lat",
    "storm_centroid_lon",
    "price_7d_avg",
    "price_pct_change",
]
LABEL_COL = "label"
THRESHOLD = 0.65


def run_backtest(n_splits: int = 5) -> pd.DataFrame:
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
            mlflow.log_metrics({
                "backtest_mean_auc": results_df["auc"].mean(),
                "backtest_mean_precision": results_df["precision"].mean(),
                "backtest_mean_recall": results_df["recall"].mean(),
            })
        print(f"Backtest run {run.info.run_id} — {len(results)} folds")
        print(results_df.to_string(index=False))

    return results_df


if __name__ == "__main__":
    run_backtest()
