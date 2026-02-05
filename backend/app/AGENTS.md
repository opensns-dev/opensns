# BACKEND APP MODULE

## OVERVIEW

FastAPI application with SQLModel ORM, LangGraph agent orchestration, and pluggable AI engine adapters.

## STRUCTURE

```
app/
├── main.py          # FastAPI app, middleware, router registration
├── db.py            # Database init (SQLite/PostgreSQL)
├── initializers.py  # Engine registration on startup
├── api/             # FastAPI routers (auth, campaigns, billing, etc.)
├── core/            # Cross-cutting: config, auth, interfaces, registry
├── models/          # SQLModel entities + Pydantic schemas
└── services/        # Business logic layer
    ├── agents/      # LangGraph workflow (see subdirectory AGENTS.md)
    ├── image/       # Image generation adapters (Fal, ComfyUI)
    ├── video/       # Video generation adapters
    └── *.py         # LLM adapters, research, scraper, etc.
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new API route | `api/{domain}.py` | Create router, register in `main.py` |
| Database model | `models/models.py` | All models in one file |
| Auth logic | `core/auth.py` | JWT creation/validation, `get_current_user` |
| New LLM/Image adapter | `services/` | Implement interface from `core/interfaces.py` |
| New Video adapter | `services/video/` | Implement interface from `services/video/interfaces.py` |
| Config/env vars | `core/config.py` | Pydantic settings |

## CONVENTIONS

### Router Pattern
```python
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user

router = APIRouter(prefix="/resource", tags=["resource"])

@router.get("/")
async def list_resources(user: User = Depends(get_current_user)):
    ...
```

### Service/Adapter Pattern
- LLM/Image engines implement abstract base from `core/interfaces.py`
- Video engines implement abstract base from `services/video/interfaces.py`
- Register in `initializers.py` via `engine_registry`
- Retrieve via `engine_registry.get_llm_engine("name")`, `get_image_engine()`, `get_video_engine()`
- Available engines: openai, ollama, fallback (LLM); fal, flux-pro, comfyui (Image); fal-video, runway, comfyui-video (Video)

### Error Handling
- Custom exceptions in `core/exceptions.py`
- Centralized handlers in `core/error_handlers.py`
- Return structured JSON: `{"error": {"code": "...", "message": "..."}}`

## KEY FILES

| File | Purpose |
|------|---------|
| `core/config.py` | Settings singleton from env |
| `core/registry.py` | Engine registry (LLM, Image, Video) |
| `core/interfaces.py` | `BaseLLMAdapter`, `BaseImageAdapter` |
| `services/video/interfaces.py` | `BaseVideoAdapter` |
| `services/usage.py` | Credit charging (`use_image_credits`, `use_video_credits`) |
| `services/pipeline.py` | Campaign execution orchestration |
| `api/billing.py` | Paddle webhook, subscription management |

## ANTI-PATTERNS

- **NEVER** call external APIs in route handlers directly (use services)
- **NEVER** store API keys unencrypted (use `core/encryption.py`)
- **NEVER** skip engine fallback (always catch `EngineNotFoundError`)
- **NEVER** block event loop (all I/O must be `async`)

## TESTING

```bash
pytest -v                    # All tests
pytest tests/test_auth.py    # Specific module
```
Test fixtures in `tests/conftest.py`. Uses SQLite in-memory for isolation.
