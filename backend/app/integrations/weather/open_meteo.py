"""Open-Meteo weather provider adapter.

Documentation:
  - Forecast:   https://open-meteo.com/en/docs
  - Geocoding:  https://open-meteo.com/en/docs/geocoding-api
  - Historical: https://open-meteo.com/en/docs/historical-weather-api

Open-Meteo is free for non-commercial use and requires no API key.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.integrations.weather.base import WeatherProviderBase

logger = logging.getLogger(__name__)

# ---------- WMO weather code → (description, emoji) ----------
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle (light)", "🌧️"),
    57: ("Freezing drizzle (dense)", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain (light)", "🌧️"),
    67: ("Freezing rain (heavy)", "🌧️"),
    71: ("Slight snowfall", "🌨️"),
    73: ("Moderate snowfall", "🌨️"),
    75: ("Heavy snowfall", "❄️"),
    77: ("Snow grains", "🌨️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "🌧️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def _wmo(code: int | None) -> tuple[str, str]:
    """Resolve a WMO weather code to (condition, icon)."""
    if code is None:
        return ("Unknown", "❓")
    return WMO_CODES.get(code, ("Unknown", "❓"))


class OpenMeteoProvider(WeatherProviderBase):
    """Adapter for the Open-Meteo public APIs."""

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.OPEN_METEO_BASE_URL.rstrip("/")
        self._geo = s.OPEN_METEO_GEOCODING_URL.rstrip("/")
        self._timeout = s.WEATHER_REQUEST_TIMEOUT

    # ------------------------------------------------------------------ #
    #  Geocoding                                                          #
    # ------------------------------------------------------------------ #

    async def geocode(self, query: str) -> list[dict]:
        """Search for locations by name via Open-Meteo geocoding API."""
        url = f"{self._geo}/search"
        params = {"name": query, "count": 5, "language": "en", "format": "json"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        return [
            {
                "name": r.get("name", ""),
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "country": r.get("country", ""),
                "admin1": r.get("admin1", ""),
                "population": r.get("population"),
            }
            for r in results
        ]

    # ------------------------------------------------------------------ #
    #  Current weather                                                    #
    # ------------------------------------------------------------------ #

    async def current_weather(self, latitude: float, longitude: float) -> dict:
        """Fetch current conditions from Open-Meteo."""
        url = f"{self._base}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join([
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "surface_pressure",
                "precipitation",
                "cloud_cover",
                "weather_code",
            ]),
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        cur = data.get("current", {})
        condition, icon = _wmo(cur.get("weather_code"))

        return {
            "datetime": cur.get("time", ""),
            "temp": cur.get("temperature_2m", 0),
            "feels_like": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "wind": cur.get("wind_speed_10m"),
            "wind_direction": cur.get("wind_direction_10m"),
            "pressure": cur.get("surface_pressure"),
            "precipitation": cur.get("precipitation"),
            "cloud_cover": cur.get("cloud_cover"),
            "condition": condition,
            "icon": icon,
            "data_source": "open-meteo",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  Forecast                                                           #
    # ------------------------------------------------------------------ #

    async def forecast(self, latitude: float, longitude: float) -> dict:
        """Fetch hourly (next 24 h) and daily (7 days) forecast."""
        url = f"{self._base}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,weather_code",
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "weather_code",
            ]),
            "forecast_hours": 24,
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        # --- Hourly ---
        hourly_raw = data.get("hourly", {})
        times = hourly_raw.get("time", [])
        temps = hourly_raw.get("temperature_2m", [])
        codes = hourly_raw.get("weather_code", [])

        hourly: list[dict] = []
        for i, t in enumerate(times):
            if i >= 24:
                break
            _, ic = _wmo(codes[i] if i < len(codes) else None)
            try:
                dt = datetime.fromisoformat(t)
                label = "Now" if i == 0 else dt.strftime("%-I %p").lstrip("0") if hasattr(dt, "strftime") else t
                # Windows strftime doesn't support %-I, fall back
            except Exception:
                label = t
            try:
                label = "Now" if i == 0 else datetime.fromisoformat(t).strftime("%I %p").lstrip("0")
            except Exception:
                pass
            hourly.append({
                "time": label,
                "icon": ic,
                "temp": temps[i] if i < len(temps) else 0,
            })

        # --- Daily ---
        daily_raw = data.get("daily", {})
        d_times = daily_raw.get("time", [])
        d_max = daily_raw.get("temperature_2m_max", [])
        d_min = daily_raw.get("temperature_2m_min", [])
        d_precip = daily_raw.get("precipitation_sum", [])
        d_prob = daily_raw.get("precipitation_probability_max", [])
        d_wind = daily_raw.get("wind_speed_10m_max", [])
        d_codes = daily_raw.get("weather_code", [])

        daily: list[dict] = []
        for i, t in enumerate(d_times):
            cond, ic = _wmo(d_codes[i] if i < len(d_codes) else None)
            try:
                dt = datetime.fromisoformat(t)
                label = "Today" if i == 0 else dt.strftime("%a")
            except Exception:
                label = t
            daily.append({
                "day": label,
                "icon": ic,
                "min": d_min[i] if i < len(d_min) else 0,
                "max": d_max[i] if i < len(d_max) else 0,
                "precipitation_probability": d_prob[i] if i < len(d_prob) else None,
                "precipitation": d_precip[i] if i < len(d_precip) else None,
                "wind_speed": d_wind[i] if i < len(d_wind) else None,
                "condition": cond,
            })

        return {"hourly": hourly, "daily": daily}
