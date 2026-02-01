---
title: Configuration
description: Environment variables and configuration options
---

import { Aside } from '@astrojs/starlight/components';

OpenSNS is configured through environment variables. This guide covers all available options.

## Backend Configuration

Create a `.env` file in the `backend/` directory:

```bash
cp backend/.env.example backend/.env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for JWT tokens (min 32 chars) | `your-super-secret-key-min-32-chars` |
| `API_KEY_ENCRYPTION_KEY` | Key for encrypting stored API keys | `your-32-byte-encryption-key-here` |

<Aside type="caution">
Generate secure random keys for production:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
</Aside>

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./opensns.db` |

For PostgreSQL (recommended for production):
```
DATABASE_URL=postgresql://user:password@localhost:5432/opensns
```

### AI Engine API Keys

These can also be configured per-user in the Settings UI:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models |
| `FAL_KEY` | Fal.ai API key for image/video generation |

### Default Engine Selection

| Variable | Options | Default |
|----------|---------|---------|
| `DEFAULT_LLM_ENGINE` | `openai`, `ollama`, `fallback` | `openai` |
| `DEFAULT_IMAGE_ENGINE` | `fal`, `comfyui` | `fal` |
| `DEFAULT_VIDEO_ENGINE` | `fal-video`, `runway`, `comfyui-video` | `fal-video` |

### Local Engine URLs

For self-hosted AI backends:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434` |
| `COMFYUI_URL` | ComfyUI WebSocket URL | `http://localhost:8188` |

### Full Example

```bash title="backend/.env"
# Project
PROJECT_NAME=OpenSNS

# Database
DATABASE_URL=sqlite:///./opensns.db

# Authentication
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AI API Keys (or configure per-user in Settings)
OPENAI_API_KEY=sk-...
FAL_KEY=...

# Default Engines
DEFAULT_LLM_ENGINE=openai
DEFAULT_IMAGE_ENGINE=fal
DEFAULT_VIDEO_ENGINE=fal-video

# Encryption
API_KEY_ENCRYPTION_KEY=your-32-byte-encryption-key-here
```

## Frontend Configuration

Create a `.env.local` file in the `frontend/` directory:

```bash
cp frontend/.env.example frontend/.env.local
```

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |

### Example

```bash title="frontend/.env.local"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Docker Configuration

When using Docker, configure via `docker-compose.yml` or environment:

```yaml title="docker-compose.yml"
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/opensns
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - API_KEY_ENCRYPTION_KEY=${API_KEY_ENCRYPTION_KEY}
```

## Security Best Practices

1. **Never commit `.env` files** - They're in `.gitignore` by default
2. **Use strong random keys** - Generate with `secrets.token_urlsafe(32)`
3. **Rotate keys periodically** - Especially `JWT_SECRET_KEY`
4. **Use PostgreSQL in production** - SQLite is for development only
5. **Enable HTTPS** - Required for secure cookie handling
