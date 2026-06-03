"""Tests for signal writer."""

from unittest.mock import patch, MagicMock


SAMPLE_RESULT = {
    "signal": "BUY",
    "probability": 0.72,
    "threshold": 0.65,
    "features": {"max_wind_kt": 90.0, "active_storm_count": 1},
}


@patch("src.ml.signal_writer.requests.post")
def test_write_signal_inserts_to_supabase(mock_post, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    mock_post.return_value = MagicMock(status_code=201)
    mock_post.return_value.raise_for_status = MagicMock()

    from src.ml.signal_writer import write_signal
    write_signal(SAMPLE_RESULT)

    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["signal"] == "BUY"
    assert payload["probability"] == 0.72


@patch("src.ml.signal_writer.requests.post")
def test_write_signal_missing_env_raises(mock_post, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    import pytest
    from src.ml.signal_writer import write_signal
    with pytest.raises(EnvironmentError):
        write_signal(SAMPLE_RESULT)
