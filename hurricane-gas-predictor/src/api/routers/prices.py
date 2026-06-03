"""Gas price history endpoints."""

import os
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, Query, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


def _sb(table: str) -> str:
    return f"{os.getenv('SUPABASE_URL')}/rest/v1/{table}"


def _headers() -> dict:
    key = os.getenv("SUPABASE_KEY", "")
    return {"apikey": key, "Authorization": f"Bearer {key}"}


@router.get("/history")
def get_price_history(
    region: str = Query(default="gulf-coast"),
    grade: str = Query(default="regular"),
    days: int = Query(default=90, ge=1, le=730),  # noqa: up to 2 years
):
    """Return gas price time series for a region and grade."""
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        resp = requests.get(
            _sb("gas_prices"),
            headers={**_headers(), "Range-Unit": "items"},
            params={
                "region": f"eq.{region}",
                "grade": f"eq.{grade}",
                "period": f"gte.{since}",
                "order": "period.asc",
                "select": "period,price_usd,grade,region",
            },
        )
        resp.raise_for_status()
        return {"region": region, "grade": grade, "prices": resp.json()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/latest")
def get_latest_prices():
    """Return the most recent price for every grade."""
    try:
        resp = requests.get(
            _sb("gas_prices"),
            headers=_headers(),
            params={
                "order": "period.desc",
                "limit": "9",  # 3 grades × up to 3 regions
                "select": "period,price_usd,grade,region,series",
            },
        )
        resp.raise_for_status()
        return {"prices": resp.json()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
