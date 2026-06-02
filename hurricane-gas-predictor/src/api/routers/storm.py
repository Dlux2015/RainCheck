"""Storm endpoints — active storm status and track data."""

import os

from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


def _supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


@router.get("/active")
def get_active_storms():
    """Return all currently active Atlantic storms from Supabase."""
    try:
        sb = _supabase()
        response = sb.table("storms").select("*").eq("active", True).execute()
        return {"storms": response.data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/{storm_id}/track")
def get_storm_track(storm_id: str):
    """Return ordered track points for a specific storm."""
    try:
        sb = _supabase()
        response = (
            sb.table("storm_track")
              .select("*")
              .eq("storm_id", storm_id)
              .order("recorded_at")
              .execute()
        )
        return {"storm_id": storm_id, "track": response.data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
