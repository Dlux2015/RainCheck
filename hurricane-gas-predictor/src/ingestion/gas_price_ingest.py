"""Ingest Gulf Coast gas price data from Zyla API into Delta Lake bronze layer."""

import os
from datetime import datetime

import httpx
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType
from dotenv import load_dotenv

load_dotenv()

ZYLA_BASE_URL = "https://zylalabs.com/api/392/us+gas+prices+api/1016/get+gas+prices"

BRONZE_SCHEMA = StructType([
    StructField("region", StringType(), True),
    StructField("grade", StringType(), True),
    StructField("price_usd", FloatType(), True),
    StructField("source_url", StringType(), True),
    StructField("ingested_at", TimestampType(), False),
])


def fetch_gas_prices(region: str = "gulf-coast") -> list[dict]:
    api_key = os.getenv("ZYLA_API_KEY")
    if not api_key:
        raise EnvironmentError("ZYLA_API_KEY is not set")
    response = httpx.get(
        ZYLA_BASE_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"region": region},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    now = datetime.utcnow()
    return [
        {
            "region": entry.get("region", region),
            "grade": entry.get("grade", "regular"),
            "price_usd": float(entry.get("price", 0)),
            "source_url": ZYLA_BASE_URL,
            "ingested_at": now,
        }
        for entry in (data if isinstance(data, list) else [data])
    ]


def write_bronze(records: list[dict], spark: SparkSession, delta_path: str) -> None:
    if not records:
        return
    df = spark.createDataFrame(records, schema=BRONZE_SCHEMA)
    # Bronze layer is append-only — never overwrite
    df.write.format("delta").mode("append").save(delta_path)


def run(delta_path: str = "dbfs:/delta/bronze/gas_prices") -> None:
    spark = SparkSession.builder.appName("zyla_gas_ingest").getOrCreate()
    records = fetch_gas_prices()
    write_bronze(records, spark, delta_path)
    print(f"Ingested {len(records)} gas price records → {delta_path}")


if __name__ == "__main__":
    run()
