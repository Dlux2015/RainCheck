"""Push storm records from Delta Lake silver layer into Supabase via REST API."""

import os
from datetime import timezone

import requests
from pyspark.sql import SparkSession
from dotenv import load_dotenv

load_dotenv()

DELTA_SILVER_STORMS = "/Volumes/workspace/default/raincheck/delta/silver/storms"


def _headers(key: str) -> dict:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _insert(url: str, key: str, table: str, rows: list[dict]) -> None:
    resp = requests.post(f"{url}/rest/v1/{table}", headers=_headers(key), json=rows)
    resp.raise_for_status()


def _upsert(url: str, key: str, table: str, rows: list[dict], on_conflict: str) -> None:
    h = {**_headers(key), "Prefer": f"resolution=merge-duplicates,return=minimal"}
    resp = requests.post(f"{url}/rest/v1/{table}?on_conflict={on_conflict}", headers=h, json=rows)
    resp.raise_for_status()


def _creds() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set")
    return url, key


def _to_iso(ts) -> str:
    if hasattr(ts, "astimezone"):
        if getattr(ts, "tzinfo", None) is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc).isoformat()
    return str(ts)


def push_storms(spark: SparkSession, silver_path: str = DELTA_SILVER_STORMS) -> None:
    url, key = _creds()
    df = spark.read.format("delta").load(silver_path).toPandas()
    if df.empty:
        print("No storm records to push")
        return

    latest = df.sort_values("ingested_at", ascending=False).drop_duplicates(subset=["storm_id"])

    storm_rows = [
        {
            "storm_id": str(row["storm_id"]),
            "storm_name": str(row["storm_name"]),
            "status": str(row["status"]),
            "lat": float(row["lat"]) if row["lat"] is not None else None,
            "lon": float(row["lon"]) if row["lon"] is not None else None,
            "wind_speed_kt": int(row["wind_speed_kt"]) if row["wind_speed_kt"] is not None else None,
            "active": True,
            "recorded_at": _to_iso(row["ingested_at"]),
        }
        for _, row in latest.iterrows()
    ]
    _upsert(url, key, "storms", storm_rows, on_conflict="storm_id")
    print(f"Upserted {len(storm_rows)} storm(s) to Supabase")

    track_rows = [
        {
            "storm_id": str(row["storm_id"]),
            "lat": float(row["lat"]) if row["lat"] is not None else None,
            "lon": float(row["lon"]) if row["lon"] is not None else None,
            "wind_speed_kt": int(row["wind_speed_kt"]) if row["wind_speed_kt"] is not None else None,
            "recorded_at": _to_iso(row["ingested_at"]),
        }
        for _, row in df.iterrows()
    ]
    _insert(url, key, "storm_track", track_rows)
    print(f"Appended {len(track_rows)} track point(s) to Supabase")


def push_storm_flag(active: bool) -> None:
    url, key = _creds()
    _insert(url, key, "storm_flags", [{"active": active}])
    print(f"Storm flag set: active={active}")


def run(spark: SparkSession | None = None) -> None:
    if spark is None:
        spark = SparkSession.builder.appName("supabase_writer").getOrCreate()
    df = spark.read.format("delta").load(DELTA_SILVER_STORMS).toPandas()
    push_storms(spark)
    push_storm_flag(is_active=not df.empty)


if __name__ == "__main__":
    run()
