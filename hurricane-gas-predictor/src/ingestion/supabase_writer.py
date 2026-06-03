"""Push storm records from Delta Lake silver layer into Supabase."""

import os
from datetime import timezone

from pyspark.sql import SparkSession
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def _supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


def _to_iso(ts) -> str:
    if hasattr(ts, "astimezone"):
        if getattr(ts, "tzinfo", None) is None:
            # tz-naive (e.g. from Pandas mock data) — treat as UTC
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc).isoformat()
    return str(ts)


def push_storms(spark: SparkSession, silver_path: str = "dbfs:/delta/silver/storms") -> None:
    """Upsert latest storm positions into Supabase and append track history."""
    df = spark.read.format("delta").load(silver_path).toPandas()
    if df.empty:
        print("No storm records to push")
        return

    sb = _supabase()

    # Deduplicate to latest record per storm_id for the snapshot table
    latest = (
        df.sort_values("ingested_at", ascending=False)
          .drop_duplicates(subset=["storm_id"])
    )

    storm_rows = [
        {
            "storm_id": row["storm_id"],
            "storm_name": row["storm_name"],
            "status": row["status"],
            "lat": float(row["lat"]) if row["lat"] is not None else None,
            "lon": float(row["lon"]) if row["lon"] is not None else None,
            "wind_speed_kt": int(row["wind_speed_kt"]) if row["wind_speed_kt"] is not None else None,
            "active": True,
            "recorded_at": _to_iso(row["ingested_at"]),
        }
        for _, row in latest.iterrows()
    ]

    # Upsert: insert or update on storm_id conflict
    sb.table("storms").upsert(storm_rows, on_conflict="storm_id").execute()
    print(f"Upserted {len(storm_rows)} storm(s) to Supabase")

    # Append every record to track history (full advisory log)
    track_rows = [
        {
            "storm_id": row["storm_id"],
            "lat": float(row["lat"]) if row["lat"] is not None else None,
            "lon": float(row["lon"]) if row["lon"] is not None else None,
            "wind_speed_kt": int(row["wind_speed_kt"]) if row["wind_speed_kt"] is not None else None,
            "recorded_at": _to_iso(row["ingested_at"]),
        }
        for _, row in df.iterrows()
    ]
    sb.table("storm_track").insert(track_rows).execute()
    print(f"Appended {len(track_rows)} track point(s) to Supabase")


def push_storm_flag(active: bool) -> None:
    """Write a storm-active flag row so the price-poll workflow knows to poll."""
    sb = _supabase()
    sb.table("storm_flags").insert({"active": active}).execute()
    print(f"Storm flag set: active={active}")


def run(spark: SparkSession | None = None) -> None:
    if spark is None:
        spark = SparkSession.builder.appName("supabase_writer").getOrCreate()

    df = spark.read.format("delta").load("dbfs:/delta/silver/storms").toPandas()
    is_active = not df.empty

    push_storms(spark)
    push_storm_flag(is_active)


if __name__ == "__main__":
    run()
