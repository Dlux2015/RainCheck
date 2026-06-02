"""Tests for NHC storm feed ingestion."""

from unittest.mock import patch, MagicMock
from src.ingestion.storm_ingest import fetch_nhc_feed, parse_nhc_feed

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:nhc="http://www.nhc.noaa.gov">
  <channel>
    <item>
      <title>TROPICAL STORM ALPHA Advisory 1</title>
      <guid>AL012026</guid>
      <nhc:lat>22.5N</nhc:lat>
      <nhc:lon>85.0W</nhc:lon>
      <nhc:wind>45</nhc:wind>
    </item>
  </channel>
</rss>"""


def test_parse_nhc_feed_returns_records():
    records = parse_nhc_feed(SAMPLE_XML)
    assert len(records) == 1
    assert records[0]["storm_id"] == "AL012026"
    assert records[0]["wind_speed_kt"] == "45"
    assert records[0]["storm_name"] == "TROPICAL"


def test_parse_nhc_feed_empty_channel():
    records = parse_nhc_feed('<?xml version="1.0"?><rss><channel></channel></rss>')
    assert records == []


def test_parse_nhc_feed_missing_channel():
    records = parse_nhc_feed("<rss></rss>")
    assert records == []


@patch("src.ingestion.storm_ingest.httpx.get")
def test_fetch_nhc_feed_calls_url(mock_get):
    mock_response = MagicMock()
    mock_response.text = SAMPLE_XML
    mock_get.return_value = mock_response
    result = fetch_nhc_feed("https://test.nhc.noaa.gov/feed.xml")
    mock_get.assert_called_once_with("https://test.nhc.noaa.gov/feed.xml", timeout=30)
    assert result == SAMPLE_XML


def test_parse_returns_ingested_at():
    records = parse_nhc_feed(SAMPLE_XML)
    assert records[0]["ingested_at"] is not None
