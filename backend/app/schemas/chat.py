"""WeatherGPT — Pydantic schemas for chat."""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    city: str = ""
    language: str = "en"


class ChatResponse(BaseModel):
    reply: str
