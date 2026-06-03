"""Build ML features from silver-layer storm and price data for the gold layer."""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def build_features(
    spark: SparkSession,
    silver_storms: str = "dbfs:/delta/silver/storms",
    silver_prices: str = "dbfs:/delta/silver/gas_prices",
    gold_path: str = "dbfs:/delta/gold/features",
) -> None:
    storms = spark.read.format("delta").load(silver_storms)
    prices = spark.read.format("delta").load(silver_prices)

    # Order windows by actual price period date, not ingestion time
    price_window = Window.partitionBy("region").orderBy(F.col("period").cast("timestamp")).rowsBetween(-6, 0)
    lag_window = Window.partitionBy("region").orderBy(F.col("period").cast("timestamp"))

    prices_featured = (
        prices
        .withColumn("price_7d_avg", F.avg("price_usd").over(price_window))
        .withColumn(
            "price_pct_change",
            (F.col("price_usd") - F.lag("price_usd", 1).over(lag_window))
            / F.lag("price_usd", 1).over(lag_window),
        )
    )

    # Aggregate storm activity by calendar week to align with weekly price data
    storm_agg = (
        storms
        .withColumn("week", F.date_trunc("week", F.col("ingested_at")))
        .groupBy("week")
        .agg(
            F.max("wind_speed_kt").alias("max_wind_kt"),
            F.count("storm_id").alias("active_storm_count"),
            F.avg("lat").alias("storm_centroid_lat"),
            F.avg("lon").alias("storm_centroid_lon"),
        )
    )

    # Join weekly prices to storm activity for the same calendar week;
    # fill 0 for weeks with no active storms (no storm → no wind, no count)
    features = (
        prices_featured
        .withColumn("week", F.date_trunc("week", F.col("period").cast("timestamp")))
        .join(storm_agg, "week", "left")
        .fillna(0, subset=["max_wind_kt", "active_storm_count", "storm_centroid_lat", "storm_centroid_lon"])
        .withColumn("label", F.when(F.col("price_pct_change") > 0.03, 1).otherwise(0))
    )

    features.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_path)
    print(f"Gold features: {features.count()} rows → {gold_path}")


def run(spark: SparkSession | None = None) -> None:
    if spark is None:
        spark = SparkSession.builder.appName("feature_engineering").getOrCreate()
    build_features(spark)


if __name__ == "__main__":
    run()
