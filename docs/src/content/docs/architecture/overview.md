---
title: Architecture Overview
description: System architecture and component design
---

OpenSNS follows a clean separation between frontend, backend, and AI services.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Next.js 15 Frontend                   │    │
│  │  • React Query for data fetching                        │    │
│  │  • shadcn/ui components                                 │    │
│  │  • WebSocket for real-time updates                      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Backend                       │    │
│  │  • REST API endpoints                                   │    │
│  │  • JWT authentication                                   │    │
│  │  • WebSocket handlers                                   │    │
│  │  • Rate limiting                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Research   │  │   Pipeline   │  │   Engines    │          │
│  │   Service    │  │  Orchestrator│  │   Registry   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   LangGraph Workflow                     │    │
│  │                                                          │    │
│  │   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐ │    │
│  │   │Rsrch │──▶│Strat │──▶│Copy  │──▶│Image │──▶│Video │ │    │
│  │   └──────┘   └──────┘   └──────┘   └──────┘   └──────┘ │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       External Services                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  OpenAI  │  │  Fal.ai  │  │OpenRouter│  │Replicate │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Together  │  │Stability │  │   BFL    │  │ Leonardo │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Ideogram │  │  Ollama  │  │ ComfyUI  │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (Next.js 15)

| Component | Purpose |
|-----------|---------|
| App Router | File-based routing with layouts |
| React Query | Server state management |
| shadcn/ui | Accessible UI components |
| Tailwind CSS | Utility-first styling |
| WebSocket | Real-time agent updates |

### Backend (FastAPI)

| Component | Purpose |
|-----------|---------|
| API Routes | REST endpoints for all operations |
| SQLModel | ORM with Pydantic validation |
| JWT Auth | Stateless authentication |
| WebSocket | Broadcast agent logs |
| Rate Limiting | Prevent abuse |

### Agent Layer (LangGraph)

The AI pipeline uses LangGraph for:

- **Stateful execution** - Tracks progress across nodes
- **Checkpointing** - Resume from interrupts
- **Parallel execution** - Run independent tasks concurrently
- **Error handling** - Graceful fallbacks

### Engine Registry

Pluggable AI backends:

```python
engine_registry.register_llm_engine("openai", OpenAIAdapter)
engine_registry.register_llm_engine("openrouter", OpenRouterAdapter)
engine_registry.register_image_engine("fal", FalImageAdapter)
engine_registry.register_image_engine("openrouter-image", OpenRouterImageAdapter)
engine_registry.register_image_engine("replicate", ReplicateAdapter)
```

## Data Flow

1. **User creates campaign** → API receives request
2. **Background task starts** → Pipeline orchestrator begins
3. **Research node** → Scrapes product URL
4. **Strategy node** → Generates marketing angles
5. **Copy node** → Creates ad copy for each angle/platform
6. **Image node** → Generates product images
7. **Video node** → Converts images to videos
8. **Assets saved** → Stored in database
9. **WebSocket broadcast** → UI updates in real-time

## Database Schema

```
User (1) ──────────────────── (N) Campaign
  │                                  │
  │                                  │
  └── (1) UserSettings         (N) Asset
                                     │
                               (N) AgentLog
```

## Security Model

- **JWT tokens** in Authorization header
- **Encrypted API keys** stored with Fernet
- **Rate limiting** on sensitive endpoints
- **SSRF protection** on asset export
