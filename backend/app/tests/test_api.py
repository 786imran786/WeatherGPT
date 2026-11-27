"""Tests for the WeatherGPT backend.

Uses FastAPI's TestClient (httpx-based) with mocked external API calls
so tests run without network access.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ══════════════════════════════════════════════════════════════════════
#  Fixtures — mock Open-Meteo responses
# ══════════════════════════════════════════════════════════════════════

MOCK_GEOCODE = [
    {
        "name": "Phagwara",
        "latitude": 31.224,
        "longitude": 75.77,
        "country": "India",
        "admin1": "Punjab",
        "population": 117000,
    }
]

MOCK_CURRENT = {
    "current": {
        "time": "2026-08-13T10:00",
        "temperature_2m": 32.5,
        "apparent_temperature": 35.1,
        "relative_humidity_2m": 62,
        "wind_speed_10m": 12.3,
        "wind_direction_10m": 220,
        "surface_pressure": 1008.0,
        "precipitation": 0.0,
        "cloud_cover": 45,
        "weather_code": 2,
    }
}

MOCK_FORECAST = {
    "hourly": {
        "time": [f"2026-08-13T{h:02d}:00" for h in range(24)],
        "temperature_2m": [30 + (h % 5) for h in range(24)],
        "weather_code": [2] * 24,
    },
    "daily": {
        "time": [f"2026-08-{13 + d:02d}" for d in range(7)],
        "temperature_2m_max": [34, 33, 32, 31, 32, 33, 34],
        "temperature_2m_min": [24, 25, 25, 24, 24, 25, 24],
        "precipitation_sum": [0, 2.1, 5.0, 0, 0, 1.2, 0],
        "precipitation_probability_max": [10, 60, 80, 20, 10, 50, 15],
        "wind_speed_10m_max": [12, 15, 18, 10, 11, 14, 12],
        "weather_code": [2, 61, 65, 1, 0, 61, 2],
    },
}


def _mock_httpx_get(url: str, **kwargs):
    """Return a mock httpx.Response for Open-Meteo URLs."""

    class FakeResp:
        status_code = 200

        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    if "geocoding" in url or "/search" in url:
        return FakeResp({"results": MOCK_GEOCODE})
    if "forecast" in url:
        params = kwargs.get("params", {})
        if "current" in str(params):
            return FakeResp(MOCK_CURRENT)
        return FakeResp(MOCK_FORECAST)
    return FakeResp({})


# ══════════════════════════════════════════════════════════════════════
#  Tests
# ══════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_ok(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "WeatherGPT"


class TestLocations:
    @patch("app.integrations.weather.open_meteo.httpx.AsyncClient")
    def test_search(self, mock_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=lambda url, **kw: _mock_httpx_get(url, **kw))
        mock_cls.return_value = mock_client

        resp = client.get("/api/v1/locations/search", params={"q": "Phagwara"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "Phagwara"
        assert len(body["results"]) > 0
        assert body["results"][0]["name"] == "Phagwara"

    def test_search_empty_query(self):
        resp = client.get("/api/v1/locations/search", params={"q": ""})
        assert resp.status_code == 422  # validation error


class TestWeatherByCity:
    """Test the frontend-compat /api/weather and /api/forecast endpoints."""

    @patch("app.integrations.weather.open_meteo.httpx.AsyncClient")
    def test_current_weather(self, mock_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=lambda url, **kw: _mock_httpx_get(url, **kw))
        mock_cls.return_value = mock_client

        resp = client.get("/api/weather", params={"city": "Phagwara"})
        assert resp.status_code == 200
        body = resp.json()
        assert "temp" in body
        assert "condition" in body
        assert "icon" in body
        assert body["city"] == "Phagwara, Punjab"

    @patch("app.integrations.weather.open_meteo.httpx.AsyncClient")
    def test_forecast(self, mock_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=lambda url, **kw: _mock_httpx_get(url, **kw))
        mock_cls.return_value = mock_client

        resp = client.get("/api/forecast", params={"city": "Phagwara"})
        assert resp.status_code == 200
        body = resp.json()
        assert "hourly" in body
        assert "daily" in body
        assert len(body["hourly"]) > 0
        assert len(body["daily"]) > 0
        assert "time" in body["hourly"][0]
        assert "day" in body["daily"][0]


class TestWeatherByCoords:
    @patch("app.integrations.weather.open_meteo.httpx.AsyncClient")
    def test_current_by_coords(self, mock_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=lambda url, **kw: _mock_httpx_get(url, **kw))
        mock_cls.return_value = mock_client

        resp = client.get("/api/v1/weather/current", params={"latitude": 31.22, "longitude": 75.77})
        assert resp.status_code == 200
        body = resp.json()
        assert body["temp"] == 32.5

    def test_invalid_coords(self):
        resp = client.get("/api/v1/weather/current", params={"latitude": 999, "longitude": 75.77})
        assert resp.status_code == 422


class TestAlerts:
    def test_alerts_empty(self):
        resp = client.get("/api/alerts", params={"region": "Punjab"})
        assert resp.status_code == 200
        assert resp.json() == []


class TestChat:
    @patch("app.integrations.weather.open_meteo.httpx.AsyncClient")
    def test_chat(self, mock_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=lambda url, **kw: _mock_httpx_get(url, **kw))
        mock_cls.return_value = mock_client

        resp = client.post("/api/chat", json={"message": "What's the weather?", "city": "Phagwara", "language": "en"})
        assert resp.status_code == 200
        body = resp.json()
        assert "reply" in body
        assert len(body["reply"]) > 0
