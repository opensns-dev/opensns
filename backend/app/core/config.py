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
