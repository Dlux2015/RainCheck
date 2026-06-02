"""Buy signal endpoints."""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class SignalRequest(BaseModel):
    max_wind_kt: float
    active_storm_count: int
    storm_centroid_lat: float
    storm_centroid_lon: float
    price_7d_avg: float
    price_pct_change: float


@router.post("/")
def get_signal(req: SignalRequest):
    """Return BUY or WAIT signal for the provided feature values."""
    try:
        from src.ml.predict import predict
        return predict(req.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/latest")
def get_latest_signal():
    """Return the most recently persisted buy signal from Supabase."""
    try:
        from supabase import create_client
        sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        response = (
            sb.table("signals")
              .select("*")
              .order("created_at", desc=True)
              .limit(1)
              .execute()
        )
        return response.data[0] if response.data else {"signal": "WAIT", "probability": 0.0}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
