"""WeatherGPT FastAPI application.

This is the main entry point. It wires up:
- CORS middleware
- API routers (v1 + frontend-compat)
- Centralised error handling
- Logging
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.v1.router import router as v1_router

# Services for the compat endpoints
from app.services.weather_service import (
    get_current_weather,
    get_forecast,
    get_popular_locations,
)
from app.services.chat_service import handle_chat
from app.schemas.chat import ChatRequest

settings = get_settings()
setup_logging(settings.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ── Mount v1 router ───────────────────────────────────────────────────
app.include_router(v1_router)


# ═══════════════════════════════════════════════════════════════════════
#  Frontend-compatibility routes
#
#  The existing frontend (api.js) calls:
#    GET  /api/weather?city=X
#    GET  /api/forecast?city=X
#    GET  /api/alerts?region=X
#    GET  /api/locations
#    POST /api/chat
#
#  These thin wrappers translate city-name lookups into the coordinate-
#  based services so the dashboard works without any frontend changes.
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/weather")
async def compat_weather(city: str = Query("Phagwara")):
    """Frontend compat — current weather by city name."""
    try:
        return await get_current_weather(city)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/api/forecast")
async def compat_forecast(city: str = Query("Phagwara")):
    """Frontend compat — forecast by city name."""
    try:
        return await get_forecast(city)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/api/alerts")
async def compat_alerts(region: str = Query("Punjab")):
    """Frontend compat — alerts.

    Open-Meteo does not provide region-based severe-weather alerts.
    Returns an empty list for now. A future provider can plug in here.
    """
    return []


@app.get("/api/locations")
async def compat_locations():
    """Frontend compat — popular locations with current temp + icon."""
    try:
        return await get_popular_locations()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/api/chat")
async def compat_chat(body: ChatRequest):
    """Frontend compat — chat."""
    try:
        reply = await handle_chat(body.message, body.city, body.language)
        return {"reply": reply}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Startup log ───────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    logger.info(
        "%s v%s starting — docs at http://%s:%s/docs",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.HOST,
        settings.PORT,
    )
