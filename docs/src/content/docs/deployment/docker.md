---
title: Docker Deployment
description: Deploy OpenSNS with Docker Compose
---

Docker Compose is the fastest way to deploy OpenSNS. It handles PostgreSQL, the backend API, and the frontend in a single command.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) v2.0+
- At least 4GB RAM available

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/opensns-dev/opensns.git
cd opensns
```

### 2. Configure Environment

Copy the example environment file and generate required secrets:

```bash
cp .env.example .env

# Generate required security keys
openssl rand -hex 32  # Use output for JWT_SECRET_KEY
openssl rand -hex 32  # Use output for API_KEY_ENCRYPTION_KEY
```

Edit `.env` with your generated keys:

```bash
# REQUIRED
JWT_SECRET_KEY=<your-generated-key>
API_KEY_ENCRYPTION_KEY=<your-generated-key>

# OPTIONAL - AI service API keys (users can also set in Settings UI)
OPENAI_API_KEY=sk-...
FAL_KEY=...
```

:::caution[Security Warning]
Never commit your `.env` file to version control. The file is already in `.gitignore`.
:::

### 3. Start Services

```bash
docker compose up -d
```

This starts:

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | Internal only | Database (not exposed externally) |
| Backend | 8000 | FastAPI server |
| Frontend | 3000 | Next.js app |

### 4. Verify Deployment

```bash
# Check all containers are running and healthy
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Open frontend
open http://localhost:3000
```

---

## Architecture

```
                    Internet
                       │
        ┌──────────────┴──────────────┐
        │                             │
  ┌─────▼─────┐                 ┌─────▼─────┐
  │ Frontend  │                 │  Backend  │
  │   :3000   │                 │   :8000   │
  └───────────┘                 └─────┬─────┘
        │                             │
        │      frontend-net           │
        └─────────────────────────────┘
                                      │
                                backend-net
                                      │
                              ┌───────▼───────┐
                              │  PostgreSQL   │
                              │  (internal)   │
                              └───────────────┘
```

**Network Security:**
- PostgreSQL is NOT exposed to the internet (internal network only)
- Frontend and Backend are on separate networks
- Backend bridges both networks to access the database

---

## Environment Variables

### Required

| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | `openssl rand -hex 32` |
| `API_KEY_ENCRYPTION_KEY` | AES key for API key encryption | `openssl rand -hex 32` |

### Optional - AI Engines

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM |
| `FAL_KEY` | Fal.ai API key for images/video |

### Optional - UGC Video Engines

| Variable | Description |
|----------|-------------|
| `HEYGEN_API_KEY` | HeyGen API key for AI avatar videos |
| `DID_API_KEY` | D-ID API key for AI avatar videos |
| `SADTALKER_URL` | Self-hosted SadTalker endpoint |

### Optional - Default Engines

| Variable | Options | Default |
|----------|---------|---------|
| `DEFAULT_LLM_ENGINE` | `openai`, `ollama`, `mock` | `openai` |
| `DEFAULT_IMAGE_ENGINE` | `fal`, `flux-pro`, `comfyui` | `fal` |
| `DEFAULT_VIDEO_ENGINE` | `fal-video`, `runway`, `comfyui-video` | `fal-video` |
| `DEFAULT_UGC_ENGINE` | `heygen`, `d-id`, `sadtalker` | `heygen` |

### Optional - Local/Self-hosted Engines

| Variable | Description |
|----------|-------------|
| `OLLAMA_URL` | Ollama API endpoint for local LLM |
| `COMFYUI_URL` | ComfyUI WebSocket URL |

### Optional - External Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL for email links |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL for frontend |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | WebSocket URL for frontend |

### Optional - Billing (Paddle)

| Variable | Description |
|----------|-------------|
| `PADDLE_API_KEY` | Paddle API key |
| `PADDLE_WEBHOOK_SECRET` | Paddle webhook secret |
| `PADDLE_ENVIRONMENT` | `sandbox` or `production` |

### Optional - Email & OAuth

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Resend API key for emails |
| `EMAIL_FROM` | Sender email address |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

---

## Common Operations

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

### Stop Services

```bash
# Stop but keep data
docker compose down

# Stop and remove volumes (DELETES DATA)
docker compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker compose build
docker compose up -d

# Or with version tag
VERSION=1.0.0 docker compose build
VERSION=1.0.0 docker compose up -d
```

### Database Operations

```bash
# Access PostgreSQL shell
docker compose exec postgres psql -U opensns -d opensns

# Backup database
docker compose exec postgres pg_dump -U opensns opensns > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U opensns -d opensns
```

---

## Production Considerations

### Custom Domain / HTTPS

For production with HTTPS, update these variables:

```bash
FRONTEND_URL=https://app.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

**Important:** `NEXT_PUBLIC_*` variables are baked into the frontend at build time. You must rebuild the frontend image when changing these:

```bash
docker compose build frontend
docker compose up -d
```

### Resource Limits

The default configuration includes sensible resource limits:

| Service | Memory Limit | Memory Reserved |
|---------|--------------|-----------------|
| PostgreSQL | 512MB | 256MB |
| Backend | 2GB | 512MB |
| Frontend | 512MB | 256MB |

Adjust in `docker-compose.yml` under `deploy.resources`.

### Using External Database

Remove the `postgres` service and update `DATABASE_URL`:

```yaml
backend:
  environment:
    DATABASE_URL: postgresql://user:pass@your-db-host:5432/opensns
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - Missing required env vars: Check JWT_SECRET_KEY and API_KEY_ENCRYPTION_KEY
# - Port already in use: Change port in docker-compose.yml
```

### Backend Health Check Failing

```bash
# Check if backend is starting
docker compose logs backend

# Verify database connection
docker compose exec backend python -c "from app.db import engine; print('DB OK')"
```

### Frontend Can't Reach Backend

For Docker deployments, the frontend connects to backend via the host machine:

```bash
# Verify backend is accessible
curl http://localhost:8000/health
```

If using custom domain, ensure `NEXT_PUBLIC_API_URL` was set correctly at build time.

### Out of Memory

Increase Docker's memory limit in Docker Desktop settings, or adjust container limits in `docker-compose.yml`.

---

## Next Steps

- [Production Deployment](/deployment/production) - HTTPS, security hardening, reverse proxy
- [Configuration Guide](/getting-started/configuration) - All environment variables
- [API Reference](/api/authentication) - API documentation
