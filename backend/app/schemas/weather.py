"""WeatherGPT — Pydantic schemas for weather data.

These schemas define the *normalized* response shapes the API returns,
regardless of the upstream weather provider.
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ---------- Current weather ----------

class CurrentWeather(BaseModel):
    """Normalised current-weather payload returned to the frontend."""
    city: str
    datetime: str  # ISO-8601
    temp: float  # °C
    feels_like: float | None = None  # °C
    humidity: int | None = None  # %
    wind: float | None = None  # km/h
    wind_direction: int | None = None  # degrees
    pressure: float | None = None  # hPa
    visibility: float | None = None  # km
    condition: str = ""
    icon: str = ""
    precipitation: float | None = None  # mm
    cloud_cover: int | None = None  # %
    data_source: str = "open-meteo"
    retrieved_at: str = ""  # ISO-8601


# ---------- Forecast ----------

class HourlyItem(BaseModel):
    time: str
    icon: str = ""
    temp: float


class DailyItem(BaseModel):
    day: str
    icon: str = ""
    min: float
    max: float
    precipitation_probability: int | None = None
    precipitation: float | None = None
    wind_speed: float | None = None
    condition: str = ""


class ForecastResponse(BaseModel):
    hourly: list[HourlyItem]
    daily: list[DailyItem]


# ---------- Alerts ----------

class AlertItem(BaseModel):
    level: str = "medium"  # "high" | "medium"
    title: str
    message: str
    source: str = ""
    time: str = ""


# ---------- Popular locations ----------

class PopularLocation(BaseModel):
    city: str
    temp: float
    icon: str = ""
