"""Storm endpoints — active storm status and track data."""

import os

import requests
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


def _sb(table: str) -> str:
    return f"{os.getenv('SUPABASE_URL')}/rest/v1/{table}"


def _headers() -> dict:
    key = os.getenv("SUPABASE_KEY", "")
    return {"apikey": key, "Authorization": f"Bearer {key}"}


@router.get("/active")
def get_active_storms():
    """Return all currently active Atlantic storms."""
    try:
        resp = requests.get(
            _sb("storms"),
            headers=_headers(),
            params={"active": "eq.true"},
        )
        resp.raise_for_status()
        return {"storms": resp.json()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/{storm_id}/track")
def get_storm_track(storm_id: str):
    """Return ordered track points for a specific storm."""
    try:
        resp = requests.get(
            _sb("storm_track"),
            headers=_headers(),
            params={"storm_id": f"eq.{storm_id}", "order": "recorded_at.asc"},
        )
        resp.raise_for_status()
        return {"storm_id": storm_id, "track": resp.json()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
