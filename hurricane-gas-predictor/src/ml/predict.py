"""Load registered XGBoost model and generate BUY / WAIT signals."""

import mlflow.xgboost
import numpy as np
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "hurricane-gas-signal"
MODEL_STAGE = "Production"
BUY_THRESHOLD = 0.65

FEATURE_COLS = [
    "max_wind_kt",
    "active_storm_count",
    "storm_centroid_lat",
    "storm_centroid_lon",
    "price_7d_avg",
    "price_pct_change",
]


def load_model():
    return mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")


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
    }
    print(predict(sample))
