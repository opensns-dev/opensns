from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PROJECT_NAME: str = "OpenSNS"
    DATABASE_URL: str = "sqlite:///./opensns.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Stripe
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PRICE_ID_BASIC: str | None = None
    STRIPE_PRICE_ID_PRO: str | None = None
    STRIPE_PRICE_ID_ULTRA: str | None = None

    # Credit pack price IDs (one-time purchases)
    STRIPE_PRICE_ID_CREDITS_50: str | None = None
    STRIPE_PRICE_ID_CREDITS_150: str | None = None
    STRIPE_PRICE_ID_CREDITS_500: str | None = None

    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str = "OpenSNS <noreply@opensns.dev>"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Frontend URL for Stripe redirects
    FRONTEND_URL: str = "http://localhost:3000"

    OPENAI_API_KEY: str | None = None
    FAL_KEY: str | None = None
    COMFYUI_URL: str = "http://localhost:8188"
    OLLAMA_URL: str = "http://localhost:11434"

    # Encryption key for storing user API keys
    API_KEY_ENCRYPTION_KEY: str = "default-encryption-key-change-in-production"

    DEFAULT_LLM_ENGINE: str = "openai"
    DEFAULT_IMAGE_ENGINE: str = "fal"
    DEFAULT_VIDEO_ENGINE: str = "fal-video"


settings = Settings()
