"""Ingest Gulf Coast gas price data from EIA Open Data API into Delta Lake bronze layer."""

import os
from datetime import datetime

import httpx
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType
from dotenv import load_dotenv

load_dotenv()

EIA_BASE_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"

# EIA series IDs for Gulf Coast gasoline grades (PADD 3)
EIA_SERIES = {
    "regular":  "EMM_EPMRR_PTE_R30_DPG",
    "midgrade": "EMM_EPMM_PTE_R30_DPG",
    "premium":  "EMM_EPMP_PTE_R30_DPG",
}

BRONZE_SCHEMA = StructType([
    StructField("period", StringType(), True),
    StructField("series", StringType(), True),
    StructField("region", StringType(), True),
    StructField("grade", StringType(), True),
    StructField("price_usd", FloatType(), True),
    StructField("source_url", StringType(), True),
    StructField("ingested_at", TimestampType(), False),
])


def fetch_gas_prices(region: str = "gulf-coast") -> list[dict]:
    api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        raise EnvironmentError("EIA_API_KEY is not set")

    now = datetime.utcnow()
    records = []

    for grade, series_id in EIA_SERIES.items():
        response = httpx.get(
            EIA_BASE_URL,
            params={
                "api_key": api_key,
                "frequency": "weekly",
                "data[]": "value",
                "facets[series][]": series_id,
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "length": 104,  # 2 years of weekly history; silver dedup prevents duplicates
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json().get("response", {}).get("data", [])

        for row in data:
            # EIA returns value as a string; skip null gaps in the series
            raw_value = row.get("value")
            if raw_value is None:
                continue
            records.append({
                "period": row["period"],
                "series": series_id,
                "region": region,
                "grade": grade,
                "price_usd": float(raw_value),
                "source_url": EIA_BASE_URL,
                "ingested_at": now,
            })

    return records


def write_bronze(records: list[dict], spark: SparkSession, delta_path: str) -> None:
    # Always write even when empty — creates the Delta table so silver can always read it
    df = spark.createDataFrame(records, schema=BRONZE_SCHEMA)
    df.write.format("delta").mode("append").save(delta_path)


def run(delta_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/gas_prices") -> None:
    spark = SparkSession.builder.appName("eia_gas_ingest").getOrCreate()
    records = fetch_gas_prices()
    write_bronze(records, spark, delta_path)
    print(f"Ingested {len(records)} gas price records → {delta_path}")


if __name__ == "__main__":
    run()
