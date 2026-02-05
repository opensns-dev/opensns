# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-03
**Commit:** 47eec20
**Branch:** main

## OVERVIEW

OpenSNS is an open-source AI marketing agent platform that generates ad creatives from a product URL. Monorepo with FastAPI backend (Python), Next.js 15 frontend (TypeScript), and Astro docs.

## STRUCTURE

```
opensns/
├── backend/           # FastAPI + SQLModel + LangGraph
│   ├── app/           # Main application code
│   │   ├── api/       # FastAPI routers
│   │   ├── core/      # Config, auth, interfaces, registry
│   │   ├── models/    # SQLModel database models
│   │   └── services/  # Business logic, adapters, agents
│   └── tests/         # pytest tests
├── frontend/          # Next.js 15 App Router + shadcn/ui
│   └── src/
│       ├── app/       # App Router pages
│       ├── components/# UI components (shadcn)
│       ├── hooks/     # React Query data hooks
│       ├── contexts/  # Auth context
│       ├── lib/       # API client, utils
│       └── types/     # TypeScript interfaces
├── docs/              # Astro Starlight documentation
└── docker-compose.yml
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `backend/app/api/` | Register in `main.py` |
| Add database model | `backend/app/models/models.py` | SQLModel, run migrations |
| Modify agent workflow | `backend/app/services/agents/` | LangGraph nodes in `nodes.py`, graph in `graph.py` |
| Add LLM/Image engine | `backend/app/services/` | Implement adapter interface from `core/interfaces.py` |
| Add UGC video engine | `backend/app/services/video/` | Implement `BaseVideoAdapter` with UGC methods |
| Add frontend page | `frontend/src/app/` | App Router convention |
| Add React hook | `frontend/src/hooks/` | Use React Query pattern |
| Add UI component | `frontend/src/components/ui/` | shadcn/ui style |

## ARCHITECTURE

### Pluggable Engine Pattern
```
BaseLLMAdapter           BaseImageAdapter           BaseVideoAdapter
(core/interfaces.py)     (core/interfaces.py)       (services/video/interfaces.py)
      │                        │                           │
   ┌──┴──┐               ┌─────┴─────┐              ┌──────┴──────┐
   │     │               │     │     │              │      │      │
OpenAI Ollama        Fal.ai FluxPro ComfyUI     Fal-Video Runway ComfyUI

BaseVideoAdapter (UGC-capable)
(services/video/interfaces.py)
      │
   ┌──┴──────┬──────────┐
   │         │          │
HeyGen    D-ID    SadTalker
```
- Engines registered in `core/registry.py` via `initializers.py`
- Dynamically selected per-user settings
- Fallback engines for graceful degradation
- Credits charged only for real generations (not fallbacks)
- UGC engines implement `supports_ugc()`, `generate_ugc_video()`, `list_avatars()`, `list_voices()`

### LangGraph Marketing Workflow
```
research → competitor_analysis → strategy → [approval]
                                                ↓
                                  ┌─────────────┴─────────────┐
                                  ↓                           ↓
                            copy_generation            image_generation
                                  ↓                           ↓
                         ugc_video_generation          video_generation
                                  ↓                           ↓
                                  └─────────┬─────────────────┘
                                            ↓
                                      merge_branches → platform_optimizer → performance_predictor → verification
                                                                                                          ↓
                                                                                                    [retry or END]
```

## CONVENTIONS

### Backend (Python)
- Async functions everywhere (`async def`)
- Type hints required (Pydantic/SQLModel)
- Adapters must implement base interfaces from `core/interfaces.py`
- API keys encrypted in DB via `core/encryption.py`
- Rate limiting via SlowAPI

### Frontend (TypeScript)
- `"use client"` directive for client components
- Data fetching via React Query hooks in `hooks/`
- Auth via context (`useAuth()` from `contexts/auth-context.tsx`)
- API calls through `lib/api.ts` axios instance with token interceptor
- Toast notifications via `sonner` (`<Toaster>` in layout)
- Path alias: `@/*` = `./src/*`

## ANTI-PATTERNS (THIS PROJECT)

- **NEVER** store raw API keys in user settings table (use encryption)
- **NEVER** call LLM/Image APIs directly in route handlers (use service layer)
- **NEVER** skip fallback handling when engine fails
- Frontend: **NEVER** store token outside `lib/api.ts` helpers

## COMMANDS

```bash
# Backend
cd backend && uvicorn app.main:app --reload      # Dev server
cd backend && pytest -v                           # Run tests
cd backend && ruff check app/                     # Lint

# Frontend
cd frontend && bun dev                            # Dev server (port 3000)
cd frontend && bun test                           # Vitest unit tests
cd frontend && bun e2e                            # Playwright E2E
cd frontend && bun lint                           # ESLint

# Docker
docker-compose up -d                              # Start all services
```

## ENV VARIABLES

### Backend (`backend/.env`)
- `DATABASE_URL` - PostgreSQL connection (SQLite for dev)
- `JWT_SECRET_KEY` - Auth token signing (32+ chars)
- `API_KEY_ENCRYPTION_KEY` - User API key encryption
- `OPENAI_API_KEY`, `FAL_KEY` - Default AI engines
- `HEYGEN_API_KEY`, `DID_API_KEY` - UGC video engines (optional)
- `SADTALKER_URL` - Self-hosted SadTalker endpoint (optional)
- `PADDLE_*` - Billing (Paddle, not Stripe)

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_URL` - Backend URL (default: `http://localhost:8000`)

## BILLING

Paddle integration (migrated from Stripe). Tiers: FREE → BASIC → PRO → ULTRA.
Credit-based usage: 1 credit/image, 12 credits/video.
See `backend/app/models/models.py` for `PLAN_LIMITS` and `CREDIT_COSTS`.
Credits only charged for real generations (fallback assets are free).

## NOTES

- SQLite used in dev, PostgreSQL in production
- WebSocket endpoint at `/ws/campaigns/{id}/logs` for real-time agent logs
- Approval workflow: set `requires_approval=True` to pause before generation
- Video generation only processes first image per angle (intentional)
