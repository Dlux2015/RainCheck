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

    price_window = Window.partitionBy("region").orderBy("ingested_at").rowsBetween(-6, 0)
    lag_window = Window.partitionBy("region").orderBy("ingested_at")

    prices_featured = (
        prices
        .withColumn("price_7d_avg", F.avg("price_usd").over(price_window))
        .withColumn(
            "price_pct_change",
            (F.col("price_usd") - F.lag("price_usd", 1).over(lag_window))
            / F.lag("price_usd", 1).over(lag_window),
        )
    )

    storm_agg = (
        storms
        .groupBy(F.window("ingested_at", "6 hours").alias("time_window"))
        .agg(
            F.max("wind_speed_kt").alias("max_wind_kt"),
            F.count("storm_id").alias("active_storm_count"),
            F.avg("lat").alias("storm_centroid_lat"),
            F.avg("lon").alias("storm_centroid_lon"),
        )
        .withColumn("window_start", F.col("time_window.start"))
        .drop("time_window")
    )

    features = (
        storm_agg
        .crossJoin(
            prices_featured
            .select("ingested_at", "region", "price_usd", "price_7d_avg", "price_pct_change")
            .distinct()
        )
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
