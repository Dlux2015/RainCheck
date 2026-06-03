"""Tests for HURDAT2 ingestion parser."""

from unittest.mock import patch, MagicMock
from src.ingestion.hurdat2_ingest import fetch_hurdat2, parse_hurdat2

SAMPLE_HURDAT2 = """\
AL062005,               KATRINA,     34,
20050823, 1800,  , TD, 23.1N,  75.1W,  30, 1008, ...
20050824, 0000,  , TD, 23.4N,  75.7W,  30, 1007, ...
20050824, 0600,  , TS, 23.8N,  76.2W,  35, 1004, ...
AL072005,                  RITA,     20,
20050918, 0600,  , TD, 23.5N,  75.5W,  30, 1007, ...
20050918, 1200,  , TS, 23.6N,  76.5W,  40, 1001, ...
"""

MISSING_WIND_HURDAT2 = """\
AL012000,            UNNAMED,     2,
20000601, 0000,  , HU, 25.0N,  90.0W, -999, 987, ...
20000601, 0600,  , HU, 25.5N,  90.5W,  85, 975, ...
"""


def test_parse_hurdat2_returns_track_records():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert len(records) == 5


def test_parse_hurdat2_storm_id_propagates():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert records[0]["storm_id"] == "AL062005"
    assert records[3]["storm_id"] == "AL072005"


def test_parse_hurdat2_storm_name_propagates():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert records[0]["storm_name"] == "KATRINA"
    assert records[3]["storm_name"] == "RITA"


def test_parse_hurdat2_pub_date_format():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert records[0]["pub_date"] == "20050823 1800"


def test_parse_hurdat2_lat_lon_preserved():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert records[0]["lat"] == "23.1N"
    assert records[0]["lon"] == "75.1W"


def test_parse_hurdat2_wind_preserved():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert records[0]["wind_speed_kt"] == "30"


def test_parse_hurdat2_skips_missing_wind():
    records = parse_hurdat2(MISSING_WIND_HURDAT2)
    assert len(records) == 1
    assert records[0]["wind_speed_kt"] == "85"


def test_parse_hurdat2_status_preserved():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert records[0]["status"] == "TD"
    assert records[2]["status"] == "TS"


def test_parse_hurdat2_empty_input():
    assert parse_hurdat2("") == []


def test_parse_hurdat2_ingested_at_populated():
    records = parse_hurdat2(SAMPLE_HURDAT2)
    assert all(r["ingested_at"] is not None for r in records)


@patch("src.ingestion.hurdat2_ingest.httpx.get")
def test_fetch_hurdat2_calls_url(mock_get):
    mock_response = MagicMock()
    mock_response.text = SAMPLE_HURDAT2
    mock_get.return_value = mock_response
    result = fetch_hurdat2("https://test.nhc.noaa.gov/hurdat2.txt")
    mock_get.assert_called_once_with("https://test.nhc.noaa.gov/hurdat2.txt", timeout=60)
    assert result == SAMPLE_HURDAT2
