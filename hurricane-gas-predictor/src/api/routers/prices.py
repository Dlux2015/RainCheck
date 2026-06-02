"""Gas price history endpoints."""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


def _supabase():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


@router.get("/history")
def get_price_history(
    region: str = Query(default="gulf-coast"),
    grade: str = Query(default="regular"),
    days: int = Query(default=30, ge=1, le=365),
):
    """Return gas price time series for a region and grade."""
    try:
        sb = _supabase()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        response = (
            sb.table("gas_prices")
              .select("*")
              .eq("region", region)
              .eq("grade", grade)
              .gte("ingested_at", since)
              .order("ingested_at")
              .execute()
        )
        return {"region": region, "grade": grade, "prices": response.data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/latest")
def get_latest_prices():
    """Return the most recent price for every region/grade combination."""
    try:
        sb = _supabase()
        response = (
            sb.table("gas_prices")
              .select("*")
              .order("ingested_at", desc=True)
              .limit(50)
              .execute()
        )
        return {"prices": response.data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
