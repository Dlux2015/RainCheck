"""Promote bronze records to silver: clean, validate, and deduplicate."""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def clean_storms(
    spark: SparkSession,
    bronze_path: str = "dbfs:/delta/bronze/storms",
    silver_path: str = "dbfs:/delta/silver/storms",
) -> None:
    df = spark.read.format("delta").load(bronze_path)
    silver = (
        df.dropDuplicates(["storm_id", "ingested_at"])
          .filter(F.col("storm_id").isNotNull())
          .withColumn("lat", F.col("lat").cast("double"))
          .withColumn("lon", F.col("lon").cast("double"))
          .withColumn("wind_speed_kt", F.col("wind_speed_kt").cast("integer"))
          .withColumn("processed_at", F.current_timestamp())
          .drop("raw_xml")
    )
    silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(silver_path)
    print(f"Silver storms: {silver.count()} rows → {silver_path}")


def clean_gas_prices(
    spark: SparkSession,
    bronze_path: str = "dbfs:/delta/bronze/gas_prices",
    silver_path: str = "dbfs:/delta/silver/gas_prices",
) -> None:
    df = spark.read.format("delta").load(bronze_path)
    silver = (
        df.dropDuplicates(["region", "grade", "ingested_at"])
          .filter(F.col("price_usd") > 0)
          .withColumn("processed_at", F.current_timestamp())
    )
    silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(silver_path)
    print(f"Silver gas prices: {silver.count()} rows → {silver_path}")


def clean_refineries(
    spark: SparkSession,
    bronze_path: str = "dbfs:/delta/bronze/refineries",
    silver_path: str = "dbfs:/delta/silver/refineries",
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
