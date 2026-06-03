"""Tests for signal writer."""

from unittest.mock import patch, MagicMock


SAMPLE_RESULT = {
    "signal": "BUY",
    "probability": 0.72,
    "threshold": 0.65,
    "features": {"max_wind_kt": 90.0, "active_storm_count": 1},
}


@patch("src.ml.signal_writer.create_client")
def test_write_signal_inserts_to_supabase(mock_client, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")

    mock_sb = MagicMock()
    mock_client.return_value = mock_sb

    from src.ml.signal_writer import write_signal
    write_signal(SAMPLE_RESULT)

    mock_sb.table("signals").insert.assert_called_once()
    inserted = mock_sb.table("signals").insert.call_args[0][0]
    assert inserted["signal"] == "BUY"
    assert inserted["probability"] == 0.72


@patch("src.ml.signal_writer.create_client")
def test_write_signal_missing_env_raises(mock_client, monkeypatch):
    # Remove from os.environ — write_signal reads them at call time via os.getenv()
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    import pytest
    from src.ml.signal_writer import write_signal
    with pytest.raises(EnvironmentError):
        write_signal(SAMPLE_RESULT)
