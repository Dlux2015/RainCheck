"""Tests for EIA gas price ingestion."""

from unittest.mock import patch, MagicMock
import pytest

# value is a string — matches the real EIA API response shape
EIA_RESPONSE = {
    "response": {
        "data": [
            {"period": "2026-05-26", "value": "3.456"}
        ]
    }
}


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_returns_three_grades(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = EIA_RESPONSE
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()

    assert len(records) == 3
    grades = {r["grade"] for r in records}
    assert grades == {"regular", "midgrade", "premium"}


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_correct_price(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = EIA_RESPONSE
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()

    for r in records:
        assert r["price_usd"] == pytest.approx(3.456)
        assert r["region"] == "gulf-coast"


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_stores_period(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = EIA_RESPONSE
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()

    for r in records:
        assert r["period"] == "2026-05-26"


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_stores_series(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = EIA_RESPONSE
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()

    series_ids = {r["series"] for r in records}
    assert "EMM_EPMRR_PTE_R30_DPG" in series_ids


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_skips_null_value(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "response": {"data": [{"period": "2026-05-26", "value": None}]}
    }
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()
    assert records == []


def test_fetch_gas_prices_missing_key_raises(monkeypatch):
    # Remove from os.environ — fetch_gas_prices() reads it at call time via os.getenv()
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    from src.ingestion.gas_price_ingest import fetch_gas_prices
    with pytest.raises(EnvironmentError):
        fetch_gas_prices()


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_empty_response(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"data": []}}
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()
    assert records == []
