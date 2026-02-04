from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_PATTERNS = [
    "change-in-production",
    "your-super-secret",
    "default-encryption",
    "changeme",
    "placeholder",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PROJECT_NAME: str = "OpenSNS"
    DATABASE_URL: str = "sqlite:///./opensns.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern in v.lower():
                raise ValueError(
                    f"JWT_SECRET_KEY contains placeholder pattern '{pattern}'. "
                    "Please set a secure random value."
                )
        return v

    PADDLE_API_KEY: str | None = None
    PADDLE_WEBHOOK_SECRET: str | None = None
    PADDLE_ENVIRONMENT: str = "sandbox"  # "sandbox" or "production"
    # Subscription price IDs (from Paddle dashboard)
    PADDLE_PRICE_ID_BASIC: str | None = None
    PADDLE_PRICE_ID_PRO: str | None = None
    PADDLE_PRICE_ID_ULTRA: str | None = None
    # Credit pack price IDs (one-time purchases)
    PADDLE_PRICE_ID_CREDITS_50: str | None = None
    PADDLE_PRICE_ID_CREDITS_150: str | None = None
    PADDLE_PRICE_ID_CREDITS_500: str | None = None

    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str = "OpenSNS <noreply@opensns.dev>"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Frontend URL for Stripe redirects
    FRONTEND_URL: str = "http://localhost:3000"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    OPENAI_API_KEY: str | None = None
    FAL_KEY: str | None = None
    COMFYUI_URL: str = "http://localhost:8188"
    OLLAMA_URL: str = "http://localhost:11434"

    API_KEY_ENCRYPTION_KEY: str

    @field_validator("API_KEY_ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError(
                "API_KEY_ENCRYPTION_KEY must be at least 32 characters long"
            )
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern in v.lower():
                raise ValueError(
                    f"API_KEY_ENCRYPTION_KEY contains placeholder pattern '{pattern}'. "
                    "Please set a secure random value."
                )
        return v

    DEFAULT_LLM_ENGINE: str = "openai"
    DEFAULT_IMAGE_ENGINE: str = "fal"
    DEFAULT_VIDEO_ENGINE: str = "fal-video"


def get_settings() -> Settings:
    """
    Lazy settings factory. Instantiates Settings on first call.
    This allows imports to succeed even without env vars set,
    while still validating at runtime when settings are accessed.
    """
    return Settings()


# For backwards compatibility - will raise ValidationError if env vars are missing
# This is intentional: we want the app to fail fast at startup if secrets are not configured
settings = get_settings()
