"""Ingest NOAA HURDAT2 Atlantic hurricane database into Delta Lake bronze layer."""

import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

# NOAA publishes a new file annually — update this URL or set HURDAT2_URL in .env
HURDAT2_URL = os.getenv(
    "HURDAT2_URL",
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051124.txt",
)

# Basin prefixes used in HURDAT2 storm IDs
_BASIN_PREFIXES = ("AL", "EP", "CP")



def fetch_hurdat2(url: str = HURDAT2_URL) -> str:
    response = httpx.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def parse_hurdat2(text: str) -> list[dict]:
    """Parse raw HURDAT2 text into a list of per-observation dicts.

    HURDAT2 alternates between header lines and track lines:
      Header:  AL011851,  NOT NAMED,  14,
      Track:   18510625, 0000, , HU, 28.0N, 94.8W, 80, 987, ...
    """
    records = []
    current_id = None
    current_name = None
    now = datetime.now(timezone.utc)

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]

        # Header line — identified by basin prefix in first token
        if len(parts) >= 3 and parts[0][:2] in _BASIN_PREFIXES:
            current_id = parts[0]
            raw_name = parts[1].strip()
            current_name = raw_name if raw_name else "UNNAMED"
            continue

        # Track line — needs at least 7 fields: date, time, record, status, lat, lon, wind
        if current_id and len(parts) >= 7:
            date_str = parts[0]
            time_str = parts[1].zfill(4)  # "0" → "0000"
            status = parts[3]
            lat = parts[4]
            lon = parts[5]
            wind = parts[6]

            # Skip rows where wind is -999 (missing / extratropical remnant)
            if wind.strip() == "-999":
                continue

            records.append({
                "storm_id":      current_id,
                "storm_name":    current_name,
                "status":        status,
                "pub_date":      f"{date_str} {time_str}",
                "lat":           lat,
                "lon":           lon,
                "wind_speed_kt": wind,
                "ingested_at":   now,
            })

    return records


def write_bronze(records: list[dict], spark, delta_path: str) -> None:
    from pyspark.sql.types import StructType, StructField, StringType, TimestampType
    schema = StructType([
        StructField("storm_id",      StringType(),    True),
        StructField("storm_name",    StringType(),    True),
        StructField("status",        StringType(),    True),
        StructField("pub_date",      StringType(),    True),
        StructField("lat",           StringType(),    True),
        StructField("lon",           StringType(),    True),
        StructField("wind_speed_kt", StringType(),    True),
        StructField("ingested_at",   TimestampType(), False),
    ])
    df = spark.createDataFrame(records, schema=schema)
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(delta_path)


def run(
    delta_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/storms_historical",
) -> None:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("hurdat2_ingest").getOrCreate()
    print(f"Fetching HURDAT2 from {HURDAT2_URL}")
    text = fetch_hurdat2()
    records = parse_hurdat2(text)
    write_bronze(records, spark, delta_path)
    print(f"Ingested {len(records)} HURDAT2 track records → {delta_path}")


if __name__ == "__main__":
    run()
