"""Tests for ML prediction module."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

SAMPLE_FEATURES = {
    "max_wind_kt": 90.0,
    "active_storm_count": 1,
    "storm_centroid_lat": 25.0,
    "storm_centroid_lon": -88.0,
    "price_7d_avg": 3.50,
    "price_pct_change": 0.04,
}


@patch("src.ml.predict.load_model")
def test_predict_buy_signal_above_threshold(mock_load):
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
    mock_load.return_value = mock_model

    from src.ml.predict import predict
    result = predict(SAMPLE_FEATURES)
    assert result["signal"] == "BUY"
    assert result["probability"] == pytest.approx(0.8, abs=0.001)


@patch("src.ml.predict.load_model")
def test_predict_wait_signal_below_threshold(mock_load):
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.6, 0.4]])
    mock_load.return_value = mock_model

    from src.ml.predict import predict
    result = predict(SAMPLE_FEATURES)
    assert result["signal"] == "WAIT"
    assert result["probability"] < 0.65


@patch("src.ml.predict.load_model")
def test_predict_result_contains_required_keys(mock_load):
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])
    mock_load.return_value = mock_model

    from src.ml.predict import predict
    result = predict(SAMPLE_FEATURES)
    assert {"signal", "probability", "threshold", "features"} <= result.keys()


@patch("src.ml.predict.load_model")
def test_predict_at_threshold_is_buy(mock_load):
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.35, 0.65]])
    mock_load.return_value = mock_model

    from src.ml.predict import predict
    result = predict(SAMPLE_FEATURES)
    assert result["signal"] == "BUY"
