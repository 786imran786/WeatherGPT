"""Abstract base for weather providers — provider adapter pattern."""
from abc import ABC, abstractmethod


class WeatherProviderBase(ABC):
    """Every weather provider must implement these methods."""

    @abstractmethod
    async def geocode(self, query: str) -> list[dict]:
        """Return geocoding results for *query*."""

    @abstractmethod
    async def current_weather(self, latitude: float, longitude: float) -> dict:
        """Return current weather for the given coordinates."""

    @abstractmethod
    async def forecast(self, latitude: float, longitude: float) -> dict:
        """Return hourly + daily forecast for the given coordinates."""
