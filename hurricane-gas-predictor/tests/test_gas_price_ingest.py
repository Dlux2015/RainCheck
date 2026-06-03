"""Tests for EIA gas price ingestion."""

from unittest.mock import patch, MagicMock
import pytest

EIA_RESPONSE = {
    "response": {
        "data": [
            {"period": "2026-05-26", "value": 3.456}
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


def test_fetch_gas_prices_missing_key_raises(monkeypatch):
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    import importlib
    import src.ingestion.gas_price_ingest as m
    importlib.reload(m)

    with pytest.raises(EnvironmentError):
        m.fetch_gas_prices()


@patch("src.ingestion.gas_price_ingest.httpx.get")
def test_fetch_gas_prices_empty_response(mock_get, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"data": []}}
    mock_get.return_value = mock_resp

    from src.ingestion.gas_price_ingest import fetch_gas_prices
    records = fetch_gas_prices()
    assert records == []
