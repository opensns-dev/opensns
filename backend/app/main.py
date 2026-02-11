from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.db import init_db
from app.api.campaigns import router as campaign_router
from app.api.assets import router as asset_router
from app.api.logs import router as log_router
from app.api.videos import router as video_router
from app.api.websocket import router as websocket_router
from app.api.auth import router as auth_router
from app.api.settings import router as settings_router
from app.api.billing import router as billing_router
from app.api.ugc import router as ugc_router
from app.api.repurpose import router as repurpose_router
from app.initializers import register_engines
from app.core.http_client import http_client_manager
from app.core.error_handlers import register_error_handlers
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.config import settings

MAX_REQUEST_SIZE = 10 * 1024 * 1024


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large. Maximum size is 10MB."},
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    register_engines()
    yield
    await http_client_manager.close()


app = FastAPI(
    title="OpenSNS API",
    description="Open-Source AI Marketing Agent Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

cors_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestSizeLimitMiddleware)

app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(billing_router)
app.include_router(ugc_router)
app.include_router(repurpose_router)
app.include_router(campaign_router)
app.include_router(asset_router)
app.include_router(log_router)
app.include_router(video_router)
app.include_router(websocket_router)

# Register centralized error handlers
register_error_handlers(app)


@app.get("/")
async def root():
    return {"message": "Welcome to OpenSNS API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
