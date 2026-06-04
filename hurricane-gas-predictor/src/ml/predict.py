"""Load XGBoost model from UC Volume and generate BUY / WAIT signals."""

import mlflow.xgboost
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Load directly from the UC Volume path — no model registry needed
MODEL_PATH = "/Volumes/workspace/default/raincheck/models/hurricane-gas-signal"
BUY_THRESHOLD = 0.65

FEATURE_COLS = [
    "max_wind_kt",
    "active_storm_count",
    "storm_centroid_lat",
    "storm_centroid_lon",
    "price_7d_avg",
    "price_pct_change",
    "refinery_capacity_at_risk_pct",
]


def load_model():
    return mlflow.xgboost.load_model(MODEL_PATH)


def predict(features: dict) -> dict:
    """Return a buy/wait signal with probability for given feature values."""
    model = load_model()
    X = np.array([[features[col] for col in FEATURE_COLS]], dtype=float)
    prob = float(model.predict_proba(X)[0, 1])
    return {
        "signal": "BUY" if prob >= BUY_THRESHOLD else "WAIT",
        "probability": round(prob, 4),
        "threshold": BUY_THRESHOLD,
        "features": features,
    }


if __name__ == "__main__":
    sample = {
        "max_wind_kt": 90.0,
        "active_storm_count": 1,
        "storm_centroid_lat": 26.5,
        "storm_centroid_lon": -89.0,
        "price_7d_avg": 3.45,
        "price_pct_change": 0.04,
        "refinery_capacity_at_risk_pct": 0.45,
    }
    print(predict(sample))
