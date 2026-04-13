# API Layer

**Scope:** `backend/app/api/`

## OVERVIEW

FastAPI router modules defining REST endpoints and WebSocket handlers. All routes enforce auth via `get_current_user` and delegate business logic to services.

## STRUCTURE

| File | Purpose |
|------|---------|
| `auth.py` | Login, register, Google OAuth, token refresh, email verification |
| `campaigns.py` | Campaign CRUD, approval workflow, export (ZIP) |
| `billing.py` | Paddle webhooks, subscription management, credit packs |
| `settings.py` | User settings, encrypted API key storage |
| `assets.py` | Asset listing, deletion, metadata updates |
| `videos.py` | Video generation endpoints (standard + UGC) |
| `ugc.py` | Avatar/voice listing for UGC engines (HeyGen, D-ID) |
| `repurpose.py` | Content repurposing API (URL → multi-platform) |
| `logs.py` | Campaign execution logs, agent trace retrieval |
| `websocket.py` | WebSocket handlers for real-time logs and status |

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add public endpoint | `auth.py` | Skip `get_current_user` for login/register only |
| Add protected endpoint | Any router | Use `Depends(get_current_user)` |
| Add rate limiting | Any route | Decorate with `@limiter.limit("10/minute")` |
| Register new router | `main.py` | `app.include_router(new_router)` |
| Add WebSocket stream | `websocket.py` | Use `ConnectionManager` pattern |
| Handle Paddle events | `billing.py` | Webhook signature verification in `paddle_webhook()` |

## CONVENTIONS

- Router pattern: `APIRouter(prefix="/resource", tags=["resource"])`
- Auth dependency: `current_user: User = Depends(get_current_user)`
- Rate limiting: `@limiter.limit("N/minute")` from `core.rate_limit`
- DB sessions: `session: Session = Depends(get_session)`
- Response models: Pydantic models from `models.models`
- WebSocket auth: Token via query param, verify with `verify_token()`
- NEVER call external APIs directly (use service layer)
- NEVER return raw DB models (use response schemas)

## KEY FILES

| File | Key Symbols |
|------|-------------|
| `auth.py` | `router`, `login()`, `register()`, `google_callback()` |
| `campaigns.py` | `router`, `create_campaign()`, `approve_campaign()`, `export_campaign()` |
| `billing.py` | `router`, `paddle_webhook()`, `get_subscription()` |
| `settings.py` | `router`, `get_settings()`, `update_settings()` |
| `websocket.py` | `router`, `manager`, `send_agent_log()`, `authenticate_websocket()` |
| `main.py` | `app`, router registrations, middleware stack |

## ANTI-PATTERNS

- **NEVER** skip `get_current_user` on protected routes (except auth endpoints)
- **NEVER** call LLM/image/video APIs directly in route handlers (use `services/`)
- **NEVER** store raw API keys in settings (use `encrypt_api_key()` from `core.encryption`)
- **NEVER** expose internal error details to clients (use `HTTPException` with generic messages)
