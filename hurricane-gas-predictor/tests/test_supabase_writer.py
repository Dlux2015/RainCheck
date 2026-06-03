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


@patch("src.ingestion.supabase_writer.requests.post")
def test_push_storm_flag_active(mock_post, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    mock_post.return_value = MagicMock(status_code=201)
    mock_post.return_value.raise_for_status = MagicMock()
    push_storm_flag(True)
    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload == [{"active": True}]


@patch("src.ingestion.supabase_writer.requests.post")
def test_push_storm_flag_inactive(mock_post, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    mock_post.return_value = MagicMock(status_code=201)
    mock_post.return_value.raise_for_status = MagicMock()
    push_storm_flag(False)
    payload = mock_post.call_args[1]["json"]
    assert payload == [{"active": False}]


@patch("src.ingestion.supabase_writer.requests.post")
def test_push_storms_upserts_and_appends_track(mock_post, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    mock_post.return_value = MagicMock(status_code=201)
    mock_post.return_value.raise_for_status = MagicMock()

    mock_spark = MagicMock()
    mock_spark.read.format.return_value.load.return_value.toPandas.return_value = SAMPLE_DF

    from src.ingestion.supabase_writer import push_storms
    push_storms(mock_spark)

    # Two POST calls: upsert storms + insert track
    assert mock_post.call_count == 2
    calls = [c[1]["json"] for c in mock_post.call_args_list]
    assert calls[0][0]["storm_id"] == "AL012026"
    assert calls[1][0]["storm_id"] == "AL012026"
