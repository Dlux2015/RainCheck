"""Build ML features from silver-layer storm and price data for the gold layer."""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def build_features(
    spark: SparkSession,
    silver_storms: str = "/Volumes/workspace/default/raincheck/delta/silver/storms",
    silver_prices: str = "/Volumes/workspace/default/raincheck/delta/silver/gas_prices",
    gold_path: str = "/Volumes/workspace/default/raincheck/delta/gold/features",
) -> None:
    storms = spark.read.format("delta").load(silver_storms)
    prices = spark.read.format("delta").load(silver_prices)

    # period is DateType in silver — directly orderable, no cast needed.
    # Partition by (region, grade) so each fuel type gets its own independent rolling window.
    price_window = Window.partitionBy("region", "grade").orderBy("period").rowsBetween(-6, 0)
    lag_window   = Window.partitionBy("region", "grade").orderBy("period")

    prices_featured = (
        prices
        .withColumn("price_7d_avg", F.avg("price_usd").over(price_window))
        .withColumn(
            "price_pct_change",
            (F.col("price_usd") - F.lag("price_usd", 1).over(lag_window))
            / F.lag("price_usd", 1).over(lag_window),
        )
    )

    # Align storms to calendar weeks using pub_date (NHC advisory timestamp),
    # which is more accurate than ingested_at (poll time).
    storm_agg = (
        storms
        .withColumn("week", F.date_trunc("week", F.col("pub_date")))
        .groupBy("week")
        .agg(
            F.max("wind_speed_kt").alias("max_wind_kt"),
            F.count("storm_id").alias("active_storm_count"),
            F.avg("lat").alias("storm_centroid_lat"),
            F.avg("lon").alias("storm_centroid_lon"),
        )
    )

    # storm_agg is always tiny (≤ a few hundred rows across a full season).
    # Broadcast it so Spark avoids a sort-merge join shuffle on prices_featured.
    features = (
        prices_featured
        .withColumn("week", F.date_trunc("week", F.col("period")))
        .join(F.broadcast(storm_agg), "week", "left")
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
