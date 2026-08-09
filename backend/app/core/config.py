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
    DEBUG: bool = False
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    DATABASE_URL: str = "sqlite:///./opensns.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    AUDIO_MIX_TIMEOUT_SECONDS: int = 300

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

    LEMONSQUEEZY_API_KEY: str | None = None
    LEMONSQUEEZY_WEBHOOK_SECRET: str | None = None
    LEMONSQUEEZY_STORE_ID: str | None = None
    LEMONSQUEEZY_VARIANT_ID_BASIC: str | None = None
    LEMONSQUEEZY_VARIANT_ID_BYOK: str | None = None
    LEMONSQUEEZY_VARIANT_ID_PRO: str | None = None
    LEMONSQUEEZY_VARIANT_ID_ULTRA: str | None = None
    LEMONSQUEEZY_VARIANT_ID_CREDITS_50: str | None = None
    LEMONSQUEEZY_VARIANT_ID_CREDITS_150: str | None = None
    LEMONSQUEEZY_VARIANT_ID_CREDITS_500: str | None = None

    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str = "OpenSNS <noreply@opensns.dev>"

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Frontend URL for Stripe redirects
    FRONTEND_URL: str = "http://localhost:3000"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openai/gpt-4o"
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    FAL_KEY: str | None = None
    REPLICATE_API_TOKEN: str | None = None
    TOGETHER_API_KEY: str | None = None
    STABILITY_API_KEY: str | None = None
    BFL_API_KEY: str | None = None
    LEONARDO_API_KEY: str | None = None
    IDEOGRAM_API_KEY: str | None = None
    COMFYUI_URL: str = "http://localhost:8188"
    OLLAMA_URL: str = "http://localhost:11434"

    HEYGEN_API_KEY: str | None = None
    DID_API_KEY: str | None = None
    SADTALKER_URL: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    MUBERT_ACCESS_TOKEN: str | None = None
    MUBERT_CUSTOMER_ID: str | None = None

    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    FACEBOOK_REDIRECT_URI: str = "http://localhost:8000/publishing/meta/callback"

    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://localhost:8000/publishing/x/callback"

    THREADS_APP_ID: str = ""
    THREADS_APP_SECRET: str = ""
    THREADS_REDIRECT_URI: str = "http://localhost:8000/publishing/threads/callback"

    STORAGE_ENDPOINT_URL: str | None = None
    STORAGE_ACCESS_KEY_ID: str | None = None
    STORAGE_SECRET_ACCESS_KEY: str | None = None
    STORAGE_BUCKET_NAME: str = "opensns-assets"
    STORAGE_REGION: str = "auto"
    STORAGE_PUBLIC_URL: str | None = None

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

    # Autopilot
    AUTOPILOT_ENABLED: bool = False
    INTERNAL_API_KEY: str = ""

    DEFAULT_LLM_ENGINE: str = (
        "gemini"  # openai, openrouter, anthropic, gemini, groq, ollama
    )
    DEFAULT_IMAGE_ENGINE: str = "gemini-image"  # gemini-image, fal, flux-pro, openrouter-image, openai-image, replicate, together, stability, bfl, leonardo, ideogram, comfyui
    DEFAULT_VIDEO_ENGINE: str = "gemini-video"  # gemini-video, fal-video, runway, comfyui-video
    DEFAULT_TTS_ENGINE: str = "gemini-tts"  # gemini-tts, openai-tts, elevenlabs, edge-tts
    DEFAULT_STT_ENGINE: str = "gemini-stt"  # gemini-stt, openai-stt
    DEFAULT_MUSIC_ENGINE: str = "lyria"  # lyria, static-bgm, elevenlabs-music, mubert


def get_settings() -> Settings:
    """
    Lazy settings factory. Instantiates Settings on first call.
    This allows imports to succeed even without env vars set,
    while still validating at runtime when settings are accessed.
    """
    return Settings()  # pyright: ignore[reportCallIssue]


# For backwards compatibility - will raise ValidationError if env vars are missing
# This is intentional: we want the app to fail fast at startup if secrets are not configured
settings = get_settings()
