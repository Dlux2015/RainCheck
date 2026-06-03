"""Generate a buy/wait signal from the latest gold features and persist it to Supabase."""

import os

import requests
from mlflow.exceptions import MlflowException
from dotenv import load_dotenv

load_dotenv()

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


def _latest_features(spark) -> dict | None:
    """Return the most recent feature row from the gold layer."""
    df = (
        spark.read.format("delta").load(GOLD_PATH)
             .orderBy("week", ascending=False)
             .limit(1)
             .select(*FEATURE_COLS)   # pull only the columns needed — avoids dragging all gold cols to driver
             .toPandas()
    )
    if df.empty:
        return None
    row = df.iloc[0]
    return {col: float(row[col]) for col in FEATURE_COLS if col in df.columns}


def write_signal(signal_result: dict) -> None:
    """Persist a signal dict (from predict()) to Supabase."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    resp = requests.post(
        f"{url}/rest/v1/signals",
        headers=headers,
        json={
            "signal": signal_result["signal"],
            "probability": signal_result["probability"],
            "threshold": signal_result["threshold"],
            "features": signal_result["features"],
        },
    )
    resp.raise_for_status()
    print(f"Signal persisted: {signal_result['signal']} ({signal_result['probability']:.2%})")


def run(spark=None) -> None:
    """Full pipeline: load latest features → predict → write to Supabase."""
    if spark is None:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("signal_writer").getOrCreate()

    features = _latest_features(spark)
    if features is None:
        print("No gold features available — skipping signal generation")
        return

    try:
        from src.ml.predict import predict
        result = predict(features)
        write_signal(result)
    except MlflowException as e:
        print(f"No trained model available yet — skipping signal: {e}")


if __name__ == "__main__":
    run()
