"""Weather endpoints.

Provides both coordinate-based (v1) endpoints and city-name convenience
endpoints that the existing frontend expects.
"""
from fastapi import APIRouter, Query, HTTPException

from app.services.weather_service import (
    get_current_weather,
    get_current_weather_coords,
    get_forecast,
    get_forecast_coords,
    get_popular_locations,
)

router = APIRouter(prefix="/weather", tags=["weather"])


# ── Coordinate-based (canonical v1 endpoints) ─────────────────────────

@router.get("/current")
async def current_by_coords(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Current weather by latitude / longitude."""
    try:
        return await get_current_weather_coords(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/forecast")
async def forecast_by_coords(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Hourly + daily forecast by latitude / longitude."""
    try:
        return await get_forecast_coords(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
