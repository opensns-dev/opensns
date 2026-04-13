# CORE MODULES

**Generated:** 2026-04-07
**Scope:** `backend/app/core/`

## OVERVIEW

Cross-cutting infrastructure for OpenSNS backend. Contains configuration, authentication, engine registry, encryption, rate limiting, and error handling. All modules are framework-agnostic building blocks used across the application.

## STRUCTURE

```
core/
├── config.py          # Pydantic Settings, env vars
├── auth.py            # JWT creation/validation, get_current_user
├── registry.py        # Engine registry (LLM, Image, Video adapters)
├── interfaces.py      # Abstract base classes for adapters
├── encryption.py      # API key encryption/decryption
├── rate_limit.py      # SlowAPI rate limiting setup
├── exceptions.py      # Custom exception hierarchy
├── error_handlers.py  # Global error handlers
├── http_client.py     # Shared httpx client manager
└── sanitization.py    # Input sanitization for prompts
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add config variable | `config.py` | Add to `Settings` class, validates on startup |
| Get current user | `auth.py` | Use `get_current_user` dependency in routes |
| Register new engine | `registry.py` | Call in `app/initializers.py` |
| Encrypt API key | `encryption.py` | `encrypt_api_key(key, settings.API_KEY_ENCRYPTION_KEY)` |
| Decrypt API key | `encryption.py` | `decrypt_api_key(encrypted, settings.API_KEY_ENCRYPTION_KEY)` |
| Add custom exception | `exceptions.py` | Inherit from `OpenSNSError` |
| Handle new exception | `error_handlers.py` | Add handler in `register_error_handlers()` |
| Rate limit route | `rate_limit.py` | Use `@limiter.limit("10/minute")` decorator |
| HTTP client | `http_client.py` | `await get_http_client()` or `managed_client()` context |
| Sanitize input | `sanitization.py` | `sanitize_for_prompt(text)` for LLM inputs |

## CONVENTIONS

### Engine Registration
```python
# In app/initializers.py
from app.core.registry import engine_registry

engine_registry.register_llm_engine("openai", lambda: OpenAIAdapter(api_key=...))
engine_registry.register_image_engine("fal", lambda: FalAIAdapter(api_key=...))
engine_registry.register_video_engine("heygen", lambda: HeyGenAdapter(api_key=...))
```

### Engine Retrieval
```python
from app.core.registry import engine_registry
from app.core.config import settings

llm = engine_registry.get_llm_engine(settings.DEFAULT_LLM_ENGINE)
image = engine_registry.get_image_engine(user.image_engine or settings.DEFAULT_IMAGE_ENGINE)
```

### Config Access
```python
from app.core.config import settings

# Singleton, validated on first import
database_url = settings.DATABASE_URL
```

### Encryption
```python
from app.core.encryption import encrypt_api_key, decrypt_api_key
from app.core.config import settings

encrypted = encrypt_api_key(api_key, settings.API_KEY_ENCRYPTION_KEY)
decrypted = decrypt_api_key(encrypted, settings.API_KEY_ENCRYPTION_KEY)
```

## KEY FILES

| File | Purpose |
|------|---------|
| `interfaces.py` | `BaseLLMAdapter`, `BaseImageAdapter`, `AdCreative`, `GenerationResult` |
| `registry.py` | `EngineRegistry`, `engine_registry` singleton, `get_*_engine()` methods |
| `config.py` | `Settings` (Pydantic), `get_settings()` lazy factory, env validation |
| `encryption.py` | `encrypt_api_key()`, `decrypt_api_key()`, v2 format with PBKDF2 |
| `auth.py` | `get_current_user`, `create_access_token`, `verify_password` |
| `rate_limit.py` | `limiter` singleton, per-user or IP-based keys |
| `exceptions.py` | `OpenSNSError` base, `EngineNotFoundError`, `GenerationError` |
| `error_handlers.py` | `register_error_handlers(app)`, converts exceptions to JSON |

## ANTI-PATTERNS

- **NEVER** store raw API keys in database (always encrypt via `encryption.py`)
- **NEVER** instantiate `Settings()` directly in modules (use `get_settings()` or `settings` singleton)
- **NEVER** create new `httpx.AsyncClient` per request (use `http_client_manager`)
- **NEVER** register engines outside `app/initializers.py` (keeps registration centralized)
- **NEVER** catch generic `Exception` without logging (use `error_handlers.py` pattern)
- **NEVER** skip `sanitize_for_prompt()` on user inputs going to LLMs
