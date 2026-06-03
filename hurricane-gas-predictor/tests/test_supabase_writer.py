"""Tests for Supabase storm writer."""

from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

from src.ingestion.supabase_writer import push_storm_flag


SAMPLE_DF = pd.DataFrame([{
    "storm_id": "AL012026",
    "storm_name": "ALPHA",
    "status": "TROPICAL STORM ALPHA Advisory 1",
    "lat": 22.5,
    "lon": -85.0,
    "wind_speed_kt": 45,
    "ingested_at": datetime(2026, 6, 1, 12, 0, 0),
}])


@patch("src.ingestion.supabase_writer.create_client")
def test_push_storm_flag_active(mock_client):
    mock_sb = MagicMock()
    mock_client.return_value = mock_sb
    push_storm_flag(True)
    mock_sb.table("storm_flags").insert.assert_called_once_with({"active": True})


@patch("src.ingestion.supabase_writer.create_client")
def test_push_storm_flag_inactive(mock_client):
    mock_sb = MagicMock()
    mock_client.return_value = mock_sb
    push_storm_flag(False)
    mock_sb.table("storm_flags").insert.assert_called_once_with({"active": False})


@patch("src.ingestion.supabase_writer.create_client")
@patch("src.ingestion.supabase_writer.SparkSession")
def test_push_storms_upserts_and_appends_track(mock_spark_cls, mock_client):
    mock_sb = MagicMock()
    mock_client.return_value = mock_sb

    mock_spark = MagicMock()
    mock_spark_cls.builder.appName.return_value.getOrCreate.return_value = mock_spark
    mock_spark.read.format.return_value.load.return_value.toPandas.return_value = SAMPLE_DF

    from src.ingestion.supabase_writer import push_storms
    push_storms(mock_spark)

    mock_sb.table("storms").upsert.assert_called_once()
    mock_sb.table("storm_track").insert.assert_called_once()
