"""Promote bronze records to silver: clean, validate, and deduplicate."""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def clean_storms(
    spark: SparkSession,
    bronze_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/storms",
    silver_path: str = "/Volumes/workspace/default/raincheck/delta/silver/storms",
) -> None:
    df = spark.read.format("delta").load(bronze_path)
    silver = (
        df
        # Deduplicate by advisory identity, not ingestion time
        .dropDuplicates(["storm_id", "pub_date"])
        # Filter null and empty-string storm IDs (malformed or off-season guids)
        .filter(F.col("storm_id").isNotNull() & (F.col("storm_id") != ""))
        # NHC encodes lat/lon as "22.5N" / "85.0W" — strip compass letter and sign correctly
        .withColumn("_lat_num", F.regexp_extract("lat", r"([0-9.]+)", 1).cast("double"))
        .withColumn("lat", F.when(F.col("lat").contains("S"), -F.col("_lat_num")).otherwise(F.col("_lat_num")))
        .drop("_lat_num")
        .withColumn("_lon_num", F.regexp_extract("lon", r"([0-9.]+)", 1).cast("double"))
        .withColumn("lon", F.when(F.col("lon").contains("W"), -F.col("_lon_num")).otherwise(F.col("_lon_num")))
        .drop("_lon_num")
        .withColumn("wind_speed_kt", F.col("wind_speed_kt").cast("integer"))
        # NHC pubDate format: "Wed, 03 Jun 2026 04:07:22 GMT"
        .withColumn("pub_date", F.to_timestamp("pub_date", "EEE, dd MMM yyyy HH:mm:ss z"))
        .withColumn("processed_at", F.current_timestamp())
        .drop("raw_xml")
    )
    silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(silver_path)
    print(f"Silver storms: {silver.count()} rows → {silver_path}")


def clean_gas_prices(
    spark: SparkSession,
    bronze_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/gas_prices",
    silver_path: str = "/Volumes/workspace/default/raincheck/delta/silver/gas_prices",
) -> None:
    df = spark.read.format("delta").load(bronze_path)
    silver = (
        df
        # Deduplicate by the actual price period, not ingestion time
        .dropDuplicates(["series", "period"])
        .filter(F.col("price_usd") > 0)
        .withColumn("period",    F.to_date("period"))
        # Ensure DoubleType precision is preserved after schema change in bronze
        .withColumn("price_usd", F.col("price_usd").cast("double"))
        .withColumn("processed_at", F.current_timestamp())
    )
    silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(silver_path)
    print(f"Silver gas prices: {silver.count()} rows → {silver_path}")


def clean_refineries(
    spark: SparkSession,
    bronze_path: str = "/Volumes/workspace/default/raincheck/delta/bronze/refineries",
    silver_path: str = "/Volumes/workspace/default/raincheck/delta/silver/refineries",
) -> None:
    df = spark.read.format("delta").load(bronze_path)
    silver = (
        df.dropDuplicates(["refinery_id"])
          .filter(F.col("capacity_bpd") > 0)
          .withColumn("processed_at", F.current_timestamp())
    )
    silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(silver_path)
    print(f"Silver refineries: {silver.count()} rows → {silver_path}")


def run(spark: SparkSession | None = None) -> None:
    if spark is None:
        spark = SparkSession.builder.appName("bronze_to_silver").getOrCreate()
    clean_storms(spark)
    clean_gas_prices(spark)
    clean_refineries(spark)


if __name__ == "__main__":
    run()
