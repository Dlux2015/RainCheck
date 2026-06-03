"""Ingest NHC Atlantic storm data from RSS feed into Delta Lake bronze layer."""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from dotenv import load_dotenv

load_dotenv()

NHC_RSS_URL = os.getenv("NHC_RSS_URL", "https://www.nhc.noaa.gov/nhc_at1.xml")

# Namespace as declared in the actual NHC feed (https, not http)
_NHC_NS = {"nhc": "https://www.nhc.noaa.gov"}

BRONZE_SCHEMA = StructType([
    StructField("storm_id", StringType(), True),
    StructField("storm_name", StringType(), True),
    StructField("status", StringType(), True),
    StructField("pub_date", StringType(), True),
    StructField("lat", StringType(), True),
    StructField("lon", StringType(), True),
    StructField("wind_speed_kt", StringType(), True),
    StructField("raw_xml", StringType(), True),
    StructField("ingested_at", TimestampType(), False),
])


def fetch_nhc_feed(url: str = NHC_RSS_URL) -> str:
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def _extract_storm_name(title: str) -> str:
    """Extract named storm from advisory title, e.g. 'TROPICAL STORM ALPHA Advisory 1' → 'ALPHA'."""
    parts = title.upper().split()
    if "ADVISORY" in parts:
        idx = parts.index("ADVISORY")
        return parts[idx - 1] if idx > 0 else ""
    return ""


def parse_nhc_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    records = []
    channel = root.find("channel")
    if channel is None:
        return records

    now = datetime.now(timezone.utc)
    for item in channel.findall("item"):
        title = item.findtext("title", default="")

        # Off-season placeholder — no active storm, skip
        if "no current storm" in title.lower():
            continue

        guid = item.findtext("guid", default="")
        pub_date = item.findtext("pubDate", default="")
        lat = item.findtext("nhc:lat", namespaces=_NHC_NS, default="")
        lon = item.findtext("nhc:lon", namespaces=_NHC_NS, default="")
        wind = item.findtext("nhc:wind", namespaces=_NHC_NS, default="")
        raw = ET.tostring(item, encoding="unicode")

        records.append({
            "storm_id": guid,
            "storm_name": _extract_storm_name(title),
            "status": title,
            "pub_date": pub_date,
            "lat": lat,
            "lon": lon,
            "wind_speed_kt": wind,
            "raw_xml": raw,
            "ingested_at": now,
        })
    return records


def write_bronze(records: list[dict], spark: SparkSession, delta_path: str) -> None:
    # Always write even when empty — creates the Delta table so silver can always read it
    df = spark.createDataFrame(records, schema=BRONZE_SCHEMA)
    df.write.format("delta").mode("append").save(delta_path)


def run(delta_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/storms") -> None:
    spark = SparkSession.builder.appName("nhc_storm_ingest").getOrCreate()
    try:
        xml_text = fetch_nhc_feed()
        records = parse_nhc_feed(xml_text)
    except Exception as e:
        # Transient NHC feed failure (empty body, timeout, non-XML response) —
        # write empty table so downstream silver/gold still run cleanly
        print(f"WARNING: NHC feed unavailable ({e}) — writing empty storm table")
        records = []
    write_bronze(records, spark, delta_path)
    print(f"Ingested {len(records)} storm records → {delta_path}")


if __name__ == "__main__":
    run()
