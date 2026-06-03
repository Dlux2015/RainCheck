"""Buy signal endpoints."""

import os

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


def _sb(table: str) -> str:
    return f"{os.getenv('SUPABASE_URL')}/rest/v1/{table}"


def _headers() -> dict:
    key = os.getenv("SUPABASE_KEY", "")
    return {"apikey": key, "Authorization": f"Bearer {key}"}


class SignalRequest(BaseModel):
    max_wind_kt: float
    active_storm_count: int
    storm_centroid_lat: float
    storm_centroid_lon: float
    price_7d_avg: float
    price_pct_change: float
    refinery_capacity_at_risk_pct: float = 0.0


@router.post("/")
def get_signal(req: SignalRequest):
    """Return BUY or WAIT signal and persist it to Supabase."""
    try:
        from src.ml.predict import predict
        from src.ml.signal_writer import write_signal
        result = predict(req.model_dump())
        write_signal(result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/accuracy")
def get_model_accuracy():
    """Return the most recent backtest metrics (AUC, precision, recall)."""
    try:
        resp = requests.get(
            _sb("model_metrics"),
            headers=_headers(),
            params={"order": "created_at.desc", "limit": "1"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else {}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/latest")
def get_latest_signal():
    """Return the most recently persisted buy signal."""
    try:
        resp = requests.get(
            _sb("signals"),
            headers=_headers(),
            params={"order": "created_at.desc", "limit": "1"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else {"signal": "WAIT", "probability": 0.0}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
