"""Build ML features from silver-layer storm and price data for the gold layer."""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

REFINERY_RISK_RADIUS_KM = 250.0


def _haversine_km(lat1, lon1, lat2, lon2):
    """Haversine great-circle distance as Spark Column expressions, result in km."""
    R = 6371.0
    dphi = F.radians(lat2 - lat1)
    dlambda = F.radians(lon2 - lon1)
    a = (
        F.sin(dphi / 2) * F.sin(dphi / 2)
        + F.cos(F.radians(lat1)) * F.cos(F.radians(lat2))
        * F.sin(dlambda / 2) * F.sin(dlambda / 2)
    )
    return F.lit(2.0 * R) * F.asin(F.sqrt(a))


def _refinery_risk_by_week(
    spark: SparkSession,
    storms: DataFrame,
    silver_refineries: str,
    radius_km: float = REFINERY_RISK_RADIUS_KM,
) -> DataFrame:
    """Return (week, refinery_capacity_at_risk_pct).

    For each calendar week, finds all Gulf Coast refineries within radius_km of
    any storm track point that week, sums their capacity, and divides by total
    Gulf Coast capacity.  Each refinery is counted at most once per week even if
    multiple storm observations are within range.
    """
    refs = (
        spark.read.format("delta").load(silver_refineries)
        .select(
            "refinery_id",
            F.col("lat").alias("ref_lat"),
            F.col("lon").alias("ref_lon"),
            "capacity_bpd",
        )
    )
    total_capacity = refs.agg(F.sum("capacity_bpd")).collect()[0][0] or 1.0

    return (
        storms
        .withColumn("week", F.date_trunc("week", F.col("pub_date")))
        .select("week", "lat", "lon")
        .crossJoin(F.broadcast(refs))
        .withColumn(
            "dist_km",
            _haversine_km(F.col("lat"), F.col("lon"), F.col("ref_lat"), F.col("ref_lon")),
        )
        .filter(F.col("dist_km") <= radius_km)
        .dropDuplicates(["week", "refinery_id"])
        .groupBy("week")
        .agg(
            (F.sum("capacity_bpd") / F.lit(total_capacity)).alias("refinery_capacity_at_risk_pct")
        )
    )


def build_features(
    spark: SparkSession,
    silver_storms: str = "/Volumes/workspace/default/raincheck/delta/silver/storms",
    silver_storms_historical: str = "/Volumes/workspace/default/raincheck/delta/silver/storms_historical",
    silver_prices: str = "/Volumes/workspace/default/raincheck/delta/silver/gas_prices",
    silver_refineries: str = "/Volumes/workspace/default/raincheck/delta/silver/refineries",
    gold_path: str = "/Volumes/workspace/default/raincheck/delta/gold/features",
) -> None:
    live_storms = spark.read.format("delta").load(silver_storms)

    # Union HURDAT2 historical storms when the backfill table exists
    try:
        hist_storms = spark.read.format("delta").load(silver_storms_historical)
        storms = (
            live_storms
            .unionByName(hist_storms, allowMissingColumns=True)
            .dropDuplicates(["storm_id", "pub_date"])
        )
        print(f"Using live + historical storms ({storms.count()} rows after dedup)")
    except Exception:
        storms = live_storms
        print("Historical storm table not found — using live storms only")

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

    # Refinery proximity: fraction of Gulf Coast refinery capacity within 250 km of any storm
    try:
        refinery_risk = _refinery_risk_by_week(spark, storms, silver_refineries)
    except Exception as exc:
        print(f"Refinery risk unavailable ({exc}) — refinery_capacity_at_risk_pct will be 0")
        refinery_risk = None

    # storm_agg is always tiny (≤ a few hundred rows per season).
    # Broadcast it so Spark avoids a sort-merge join shuffle on prices_featured.
    storm_agg_base = (
        storms
        .withColumn("week", F.date_trunc("week", F.col("pub_date")))
        .groupBy("week")
        .agg(
            F.max("wind_speed_kt").alias("max_wind_kt"),
            F.countDistinct("storm_id").alias("active_storm_count"),
            F.avg("lat").alias("storm_centroid_lat"),
            F.avg("lon").alias("storm_centroid_lon"),
        )
    )

    if refinery_risk is not None:
        storm_agg = (
            storm_agg_base
            .join(refinery_risk, "week", "left")
            .fillna(0.0, subset=["refinery_capacity_at_risk_pct"])
        )
    else:
        storm_agg = storm_agg_base.withColumn("refinery_capacity_at_risk_pct", F.lit(0.0))

    features = (
        prices_featured
        .withColumn("week", F.date_trunc("week", F.col("period")))
        .join(F.broadcast(storm_agg), "week", "left")
        .fillna(0, subset=[
            "max_wind_kt", "active_storm_count",
            "storm_centroid_lat", "storm_centroid_lon",
            "refinery_capacity_at_risk_pct",
        ])
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
