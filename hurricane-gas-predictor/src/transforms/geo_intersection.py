"""Intersect storm track buffers with Gulf Coast refinery locations."""

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def build_refinery_geodataframe(
    spark: SparkSession,
    silver_path: str = "/tmp/delta/silver/refineries",
) -> gpd.GeoDataFrame:
    df = spark.read.format("delta").load(silver_path).toPandas()
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )


def build_storm_track_buffer(storm_df: pd.DataFrame, radius_km: float = 250.0) -> gpd.GeoDataFrame:
    """Return a dissolved buffer polygon covering the storm's full track."""
    gdf = gpd.GeoDataFrame(
        storm_df,
        geometry=gpd.points_from_xy(storm_df["lon"], storm_df["lat"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:3857")
    gdf["geometry"] = gdf["geometry"].buffer(radius_km * 1000)
    dissolved = unary_union(gdf["geometry"])
    return gpd.GeoDataFrame(geometry=[dissolved], crs="EPSG:3857").to_crs("EPSG:4326")


def find_at_risk_refineries(
    spark: SparkSession,
    storm_id: str,
    radius_km: float = 250.0,
) -> list[str]:
    """Return refinery_ids within radius_km of any point on the storm track."""
    storms_df = (
        spark.read.format("delta")
             .load("/tmp/delta/silver/storms")
             .filter(F.col("storm_id") == storm_id)
             .toPandas()
    )
    if storms_df.empty:
        return []

    refineries = build_refinery_geodataframe(spark)
    storm_buffer = build_storm_track_buffer(storms_df, radius_km)
    at_risk = gpd.sjoin(refineries, storm_buffer, how="inner", predicate="within")
    return at_risk["refinery_id"].tolist()


if __name__ == "__main__":
    spark = SparkSession.builder.appName("geo_intersection").getOrCreate()
    ids = find_at_risk_refineries(spark, storm_id="AL012026")
    print("At-risk refineries:", ids)
