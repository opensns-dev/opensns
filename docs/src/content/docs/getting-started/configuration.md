---
title: Configuration
description: Environment variables and configuration options
---

import { Aside } from '@astrojs/starlight/components';

OpenSNS is configured through environment variables. This guide covers all available options.

## Quick Setup

### Docker (Recommended)

```bash
cp .env.example .env
# Edit .env with your settings
```

### Manual Setup

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env.local
```

---

## Required Variables

These must be set before starting OpenSNS:

| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `JWT_SECRET_KEY` | Secret for JWT tokens (min 32 chars) | `openssl rand -hex 32` |
| `API_KEY_ENCRYPTION_KEY` | Key for encrypting stored API keys | `openssl rand -hex 32` |

<Aside type="caution">
Generate secure random keys for production:
```bash
openssl rand -hex 32
```
Never use the example values in production!
</Aside>

---

## Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./opensns.db` |

For PostgreSQL (recommended for production):
```
DATABASE_URL=postgresql://user:password@localhost:5432/opensns
```

---

## AI Engine API Keys

These can be set globally (in `.env`) or per-user (in Settings UI):

### LLM & Image Engines

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models and GPT Image |
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM and image models |
| `FAL_KEY` | Fal.ai API key for image/video generation |
| `REPLICATE_API_TOKEN` | Replicate API token for image models |
| `TOGETHER_API_KEY` | Together AI API key for FLUX image models |
| `STABILITY_API_KEY` | Stability AI API key for Stable Diffusion |
| `BFL_API_KEY` | Black Forest Labs API key for FLUX |
| `LEONARDO_API_KEY` | Leonardo AI API key for image generation |
| `IDEOGRAM_API_KEY` | Ideogram API key for image generation |

### UGC Video Engines

| Variable | Description |
|----------|-------------|
| `HEYGEN_API_KEY` | HeyGen API key for AI avatar videos |
| `DID_API_KEY` | D-ID API key for AI avatar videos |
| `SADTALKER_URL` | Self-hosted SadTalker endpoint URL |

---

## Default Engine Selection

| Variable | Options | Default |
|----------|---------|---------|
| `DEFAULT_LLM_ENGINE` | `openai`, `openrouter`, `anthropic`, `gemini`, `groq`, `ollama` | `openai` |
| `DEFAULT_IMAGE_ENGINE` | `fal`, `flux-pro`, `openrouter-image`, `openai-image`, `replicate`, `together`, `stability`, `bfl`, `leonardo`, `ideogram`, `comfyui` | `fal` |
| `DEFAULT_VIDEO_ENGINE` | `fal-video`, `runway`, `comfyui-video` | `fal-video` |
| `DEFAULT_UGC_ENGINE` | `heygen`, `d-id`, `sadtalker` | `heygen` |

---

## Local/Self-hosted Engine URLs

For self-hosted AI backends:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434` |
| `COMFYUI_URL` | ComfyUI WebSocket URL | `http://localhost:8188` |
| `SADTALKER_URL` | SadTalker API endpoint | (none) |

---

## Frontend Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for real-time logs | `ws://localhost:8000` |

<Aside type="note">
`NEXT_PUBLIC_*` variables are embedded at build time. When using Docker, you must rebuild the frontend image if these change.
</Aside>

---

## CORS & URLs

| Variable | Description | Default |
|----------|-------------|---------|
| `FRONTEND_URL` | Frontend URL (for email links) | `http://localhost:3000` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |

---

## Billing (Paddle)

| Variable | Description |
|----------|-------------|
| `PADDLE_API_KEY` | Paddle API key |
| `PADDLE_WEBHOOK_SECRET` | Paddle webhook secret |
| `PADDLE_ENVIRONMENT` | `sandbox` or `production` |
| `PADDLE_PRICE_ID_BASIC` | Price ID for Basic plan |
| `PADDLE_PRICE_ID_PRO` | Price ID for Pro plan |
| `PADDLE_PRICE_ID_ULTRA` | Price ID for Ultra plan |
| `PADDLE_PRICE_ID_CREDITS_50` | Price ID for 50 credits pack |
| `PADDLE_PRICE_ID_CREDITS_150` | Price ID for 150 credits pack |
| `PADDLE_PRICE_ID_CREDITS_500` | Price ID for 500 credits pack |

---

## Email (Resend)

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Resend API key for transactional emails |
| `EMAIL_FROM` | Sender email address (e.g., `OpenSNS <noreply@yourdomain.com>`) |

---

## OAuth

### Google

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

---

## Full Example

### Docker (.env in project root)

```bash title=".env"
# ===========================================
# REQUIRED
# ===========================================
JWT_SECRET_KEY=your-64-char-hex-key-from-openssl-rand
API_KEY_ENCRYPTION_KEY=your-64-char-hex-key-from-openssl-rand

# ===========================================
# AI ENGINES (optional - users can set in UI)
# ===========================================
OPENROUTER_API_KEY=...

# UGC Video
HEYGEN_API_KEY=...
DID_API_KEY=...

# ===========================================
# DEFAULT ENGINES
# ===========================================
DEFAULT_LLM_ENGINE=openrouter
DEFAULT_IMAGE_ENGINE=openrouter-image
DEFAULT_VIDEO_ENGINE=fal-video
DEFAULT_UGC_ENGINE=heygen

# ===========================================
# URLS (change for production)
# ===========================================
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Backend (backend/.env)

```bash title="backend/.env"
DATABASE_URL=sqlite:///./opensns.db

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

API_KEY_ENCRYPTION_KEY=your-encryption-key

OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=...
FAL_KEY=...

DEFAULT_LLM_ENGINE=openrouter
DEFAULT_IMAGE_ENGINE=openrouter-image
DEFAULT_VIDEO_ENGINE=fal-video
DEFAULT_UGC_ENGINE=heygen
```

### Frontend (frontend/.env.local)

```bash title="frontend/.env.local"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Security Best Practices

1. **Never commit `.env` files** - They're in `.gitignore` by default
2. **Use strong random keys** - Generate with `openssl rand -hex 32`
3. **Rotate keys periodically** - Especially `JWT_SECRET_KEY`
4. **Use PostgreSQL in production** - SQLite is for development only
5. **Enable HTTPS** - Required for secure cookie handling
6. **Restrict CORS origins** - Only allow your actual frontend domain

---

## Next Steps

- [Docker Deployment](/deployment/docker) - Deploy with Docker Compose
- [Production Deployment](/deployment/production) - HTTPS, security hardening
- [Architecture Overview](/architecture/overview) - Understand the system
