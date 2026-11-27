"""Location service — geocode and popular-location helpers."""
from __future__ import annotations

import logging

from app.integrations.weather.open_meteo import OpenMeteoProvider

logger = logging.getLogger(__name__)

_provider = OpenMeteoProvider()


async def search_locations(query: str) -> list[dict]:
    """Geocode a city / location name and return matching results."""
    if not query or not query.strip():
        return []
    return await _provider.geocode(query.strip())


async def geocode_city(city: str) -> dict | None:
    """Resolve a city name to its first geocoding match (lat/lon)."""
    results = await search_locations(city)
    return results[0] if results else None
