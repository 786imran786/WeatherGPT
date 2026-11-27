"""WeatherGPT — Pydantic schemas for location data."""
from pydantic import BaseModel, Field


class LocationResult(BaseModel):
    """A single geocoding result."""
    name: str
    latitude: float
    longitude: float
    country: str = ""
    admin1: str = ""  # state / province / region
    population: int | None = None

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.admin1:
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


class LocationSearchResponse(BaseModel):
    """Response for GET /api/v1/locations/search."""
    query: str
    results: list[LocationResult]
