"""Seed Gulf Coast refinery location and capacity data into bronze layer (EIA public data)."""

from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType

BRONZE_SCHEMA = StructType([
    StructField("refinery_id",  StringType(),    False),
    StructField("name",         StringType(),    True),
    StructField("state",        StringType(),    True),
    StructField("lat",          FloatType(),     True),
    StructField("lon",          FloatType(),     True),
    StructField("capacity_bpd", FloatType(),     True),
    StructField("source",       StringType(),    True),
    StructField("ingested_at",  TimestampType(), False),
])

# EIA public dataset — major Gulf Coast refineries
GULF_COAST_REFINERIES = [
    {"refinery_id": "TX-001", "name": "Port Arthur Refinery", "state": "TX", "lat": 29.899, "lon": -93.921, "capacity_bpd": 600000.0},
    {"refinery_id": "TX-002", "name": "Beaumont Refinery",    "state": "TX", "lat": 30.080, "lon": -94.102, "capacity_bpd": 366000.0},
    {"refinery_id": "LA-001", "name": "Baton Rouge Refinery", "state": "LA", "lat": 30.447, "lon": -91.154, "capacity_bpd": 502000.0},
    {"refinery_id": "LA-002", "name": "Norco Refinery",       "state": "LA", "lat": 29.993, "lon": -90.415, "capacity_bpd": 255000.0},
    {"refinery_id": "MS-001", "name": "Pascagoula Refinery",  "state": "MS", "lat": 30.359, "lon": -88.557, "capacity_bpd": 356000.0},
]


def write_bronze(spark: SparkSession, delta_path: str) -> None:
    now = datetime.now(timezone.utc)
    records = [{**r, "source": "EIA-public", "ingested_at": now} for r in GULF_COAST_REFINERIES]
    df = spark.createDataFrame(records, schema=BRONZE_SCHEMA)
    # Bronze layer is append-only — never overwrite
    df.write.format("delta").mode("append").save(delta_path)


def run(delta_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/refineries") -> None:
    spark = SparkSession.builder.appName("refinery_ingest").getOrCreate()
    write_bronze(spark, delta_path)
    print(f"Seeded {len(GULF_COAST_REFINERIES)} refinery records → {delta_path}")


if __name__ == "__main__":
    run()
