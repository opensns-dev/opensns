from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
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
from app.api.templates import router as templates_router
from app.api.brand_kits import router as brand_kits_router
from app.api.publishing import router as publishing_router
from app.api.variants import router as variants_router
from app.api.team import router as team_router
from app.api.api_keys import router as api_keys_router
from app.api.scheduling import router as scheduling_router
from app.api.custom_media import router as custom_media_router
from app.api.white_label import router as white_label_router
from app.api.ad_serving import serve_router
from app.api.product_photos import router as product_photos_router
from app.api.ai_labeling import router as ai_labeling_router
from app.api.providers import router as providers_router
from app.api.audio import router as audio_router
from app.api.waitlist import router as waitlist_router
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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment="production" if not settings.DEBUG else "development",
            send_default_pii=False,
        )
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
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(billing_router)
app.include_router(ugc_router)
app.include_router(repurpose_router)
app.include_router(templates_router)
app.include_router(brand_kits_router)
app.include_router(publishing_router)
app.include_router(variants_router)
app.include_router(campaign_router)
app.include_router(asset_router)
app.include_router(log_router)
app.include_router(video_router)
app.include_router(websocket_router)
app.include_router(team_router)
app.include_router(api_keys_router)
app.include_router(scheduling_router)
app.include_router(custom_media_router)
app.include_router(white_label_router)
app.include_router(serve_router)
app.include_router(product_photos_router)
app.include_router(ai_labeling_router)
app.include_router(providers_router)
app.include_router(audio_router, prefix="/api")
app.include_router(waitlist_router)

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
