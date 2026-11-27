"""Weather service — business logic between API routes and providers."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import get_settings
from app.integrations.weather.open_meteo import OpenMeteoProvider
from app.services.location_service import geocode_city

logger = logging.getLogger(__name__)

_provider = OpenMeteoProvider()


async def get_current_weather(city: str) -> dict:
    """Get current weather by city name.

    Geocodes the city, then fetches current conditions.
    Returns the dict expected by the frontend's ``renderWeather()``.
    """
    loc = await geocode_city(city)
    if loc is None:
        raise ValueError(f"City not found: {city}")

    data = await _provider.current_weather(loc["latitude"], loc["longitude"])

    display = loc["name"]
    if loc.get("admin1"):
        display += f", {loc['admin1']}"

    data["city"] = display
    # Provide visibility in km — Open-Meteo current doesn't expose this
    # directly, so we set a sensible placeholder.
    if data.get("visibility") is None:
        data["visibility"] = 10  # default 10 km when unavailable
    return data


async def get_forecast(city: str) -> dict:
    """Get hourly + daily forecast by city name."""
    loc = await geocode_city(city)
    if loc is None:
        raise ValueError(f"City not found: {city}")
    return await _provider.forecast(loc["latitude"], loc["longitude"])


async def get_current_weather_coords(latitude: float, longitude: float, label: str = "") -> dict:
    """Get current weather by coordinates."""
    data = await _provider.current_weather(latitude, longitude)
    data["city"] = label or f"{latitude:.2f}, {longitude:.2f}"
    if data.get("visibility") is None:
        data["visibility"] = 10
    return data


async def get_forecast_coords(latitude: float, longitude: float) -> dict:
    """Get forecast by coordinates."""
    return await _provider.forecast(latitude, longitude)


async def get_popular_locations() -> list[dict]:
    """Return current weather snapshots for popular cities (dashboard sidebar)."""
    settings = get_settings()
    cities = settings.POPULAR_CITIES

    async def _fetch_one(city_name: str) -> dict | None:
        try:
            w = await get_current_weather(city_name)
            return {"city": city_name, "temp": w["temp"], "icon": w["icon"]}
        except Exception as exc:
            logger.warning("Failed to fetch weather for %s: %s", city_name, exc)
            return None

    results = await asyncio.gather(*[_fetch_one(c) for c in cities])
    return [r for r in results if r is not None]
