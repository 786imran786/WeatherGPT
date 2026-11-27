"""Location endpoints."""
from fastapi import APIRouter, Query, HTTPException

from app.services.location_service import search_locations

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/search")
async def location_search(q: str = Query(..., min_length=1, description="City or location name")):
    """Search for locations by name via geocoding."""
    try:
        results = await search_locations(q)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding service error: {exc}")
    return {"query": q, "results": results}
