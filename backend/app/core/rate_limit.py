import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.auth import verify_token, ACCESS_TOKEN_COOKIE_NAME


def get_rate_limit_key(request: Request) -> str:
    if os.environ.get("TESTING") == "1":
        return get_remote_address(request)

    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)

    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        payload = verify_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"

    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    enabled=os.environ.get("TESTING") != "1",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail,
        },
    )
