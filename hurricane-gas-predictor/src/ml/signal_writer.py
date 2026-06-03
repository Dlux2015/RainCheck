"""Generate a buy/wait signal from the latest gold features and persist it to Supabase."""

import os

from pyspark.sql import SparkSession
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

GOLD_PATH = "dbfs:/delta/gold/features"
FEATURE_COLS = [
    "max_wind_kt",
    "active_storm_count",
    "storm_centroid_lat",
    "storm_centroid_lon",
    "price_7d_avg",
    "price_pct_change",
]


def _latest_features(spark: SparkSession) -> dict | None:
    """Return the most recent feature row from the gold layer."""
    df = (
        spark.read.format("delta").load(GOLD_PATH)
             .orderBy("week", ascending=False)
             .limit(1)
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

    sb = create_client(url, key)
    sb.table("signals").insert({
        "signal": signal_result["signal"],
        "probability": signal_result["probability"],
        "threshold": signal_result["threshold"],
        "features": signal_result["features"],
    }).execute()
    print(f"Signal persisted: {signal_result['signal']} ({signal_result['probability']:.2%})")


def run(spark: SparkSession | None = None) -> None:
    """Full pipeline: load latest features → predict → write to Supabase."""
    if spark is None:
        spark = SparkSession.builder.appName("signal_writer").getOrCreate()

    features = _latest_features(spark)
    if features is None:
        print("No gold features available — skipping signal generation")
        return

    from src.ml.predict import predict
    result = predict(features)
    write_signal(result)


if __name__ == "__main__":
    run()
