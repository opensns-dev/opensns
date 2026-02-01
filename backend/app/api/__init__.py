# API Routers
from app.api.campaigns import router as campaigns_router
from app.api.assets import router as assets_router
from app.api.logs import router as logs_router
from app.api.videos import router as videos_router

__all__ = ["campaigns_router", "assets_router", "logs_router", "videos_router"]
