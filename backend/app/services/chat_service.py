"""Chat service — stub for future LLM integration.

Currently returns a helpful static reply acknowledging the query.
When an LLM provider is integrated later, this service will:
1. Parse intent from the user message.
2. Call weather / location tools.
3. Format a natural-language response with real data.
"""
from __future__ import annotations

import logging

from app.services.weather_service import get_current_weather, get_forecast

logger = logging.getLogger(__name__)


async def handle_chat(message: str, city: str = "", language: str = "en") -> str:
    """Process a chat message and return a reply string.

    For now, we do basic keyword matching to return real weather data.
    Full LLM integration will replace this logic.
    """
    msg_lower = message.lower()

    # Try to extract a city from the message if not provided
    target_city = city or "Phagwara"

    try:
        if any(kw in msg_lower for kw in ["forecast", "5-day", "week", "daily", "tomorrow"]):
            fc = await get_forecast(target_city)
            daily = fc.get("daily", [])
            if daily:
                lines = [f"📅 Forecast for {target_city}:"]
                for d in daily[:5]:
                    lines.append(
                        f"  {d['icon']} {d['day']}: {d['min']:.0f}°C – {d['max']:.0f}°C, {d.get('condition', '')}"
                    )
                return "\n".join(lines)
            return f"Could not retrieve forecast for {target_city}."

        # Default: current weather
        w = await get_current_weather(target_city)
        return (
            f"{w['icon']} Current weather in {w['city']}:\n"
            f"🌡️ {w['temp']:.1f}°C (feels like {w.get('feels_like', '?')}°C)\n"
            f"💧 Humidity: {w.get('humidity', '?')}%\n"
            f"💨 Wind: {w.get('wind', '?')} km/h\n"
            f"☁️ {w['condition']}"
        )
    except Exception as exc:
        logger.exception("Chat handler error")
        return f"Sorry, I couldn't retrieve weather data for {target_city}. Error: {exc}"
