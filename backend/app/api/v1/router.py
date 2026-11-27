"""V1 API router — aggregates all v1 endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import health, locations, weather, chat

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(locations.router)
router.include_router(weather.router)
router.include_router(chat.router)
