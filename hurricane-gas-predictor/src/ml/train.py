"""Train XGBoost buy-signal model and save to UC Volume."""

import numpy as np
import xgboost as xgb
from pyspark.sql import SparkSession
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score
from dotenv import load_dotenv

load_dotenv()

GOLD_PATH = "/Volumes/workspace/default/raincheck/delta/gold/features"
MODEL_PATH = "/Volumes/workspace/default/raincheck/models/hurricane-gas-signal"

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

DEFAULT_PARAMS = {
    "n_estimators": 200,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "auc",
}


def load_features(spark: SparkSession) -> tuple[np.ndarray, np.ndarray]:
    df = (
        spark.read.format("delta").load(GOLD_PATH)
             .toPandas()
             .dropna(subset=FEATURE_COLS + [LABEL_COL])
    )
    return df[FEATURE_COLS].values.astype(float), df[LABEL_COL].values.astype(int)


def train(params: dict | None = None) -> dict:
    """Train model, save to UC Volume, return metrics dict."""
    if params is None:
        params = DEFAULT_PARAMS

    spark = SparkSession.builder.appName("xgb_train").getOrCreate()
    X, y = load_features(spark)
    if len(X) < 10:
        raise ValueError(
            f"Training set has only {len(X)} rows after dropna — need at least 10. "
            "Run the ETL job first to populate gold features."
        )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    probs = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probs)
    f1  = f1_score(y_test, (probs >= 0.5).astype(int))

    import mlflow.xgboost
    mlflow.xgboost.save_model(model, MODEL_PATH)

    metrics = {"auc": round(auc, 4), "f1": round(f1, 4), "rows": len(X)}
    print(f"AUC: {auc:.4f}  F1: {f1:.4f}  rows: {len(X)}")
    print(f"Model saved → {MODEL_PATH}")
    return metrics


if __name__ == "__main__":
    train()
