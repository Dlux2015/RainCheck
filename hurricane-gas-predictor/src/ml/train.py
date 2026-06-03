"""Train XGBoost buy-signal model with full MLflow tracking and model registration."""

import mlflow
import mlflow.xgboost
from mlflow import MlflowClient
from mlflow.models import infer_signature
import numpy as np
import xgboost as xgb
from pyspark.sql import SparkSession
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score
from dotenv import load_dotenv

load_dotenv()

GOLD_PATH = "/Volumes/workspace/default/raincheck/delta/gold/features"
# Workspace Model Registry — simple name, no 3-part UC syntax (Free Edition
# doesn't grant S3 write access to the UC model storage bucket)
MODEL_NAME = "hurricane-gas-signal"

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


def train(params: dict | None = None) -> str:
    """Train model, log to MLflow, register as Production in workspace registry, return run_id."""
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

    with mlflow.start_run() as run:
        mlflow.log_params(params)

        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        probs = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probs)
        f1 = f1_score(y_test, (probs >= 0.5).astype(int))
        mlflow.log_metrics({"auc": auc, "f1": f1})

        signature = infer_signature(X_train, model.predict_proba(X_train)[:, 1])
        mlflow.xgboost.log_model(model, artifact_path="model", signature=signature)
        mv = mlflow.register_model(f"runs:/{run.info.run_id}/model", MODEL_NAME)

        # Promote to Production, archive any previous Production version
        MlflowClient().transition_model_version_stage(
            MODEL_NAME, mv.version, stage="Production", archive_existing_versions=True
        )

        print(f"Run {run.info.run_id} — AUC: {auc:.4f}  F1: {f1:.4f}")
        print(f"Registered {MODEL_NAME} v{mv.version} → Production")
        return run.info.run_id


if __name__ == "__main__":
    train()
