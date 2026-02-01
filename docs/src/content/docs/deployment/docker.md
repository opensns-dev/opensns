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
git clone https://github.com/yourusername/opensns.git
cd opensns
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Required: Security keys (generate your own!)
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars-long
API_KEY_ENCRYPTION_KEY=your-encryption-key-exactly-32chars

# Optional: AI service API keys
OPENAI_API_KEY=sk-...
FAL_KEY=...

# Optional: Default engines
DEFAULT_LLM_ENGINE=openai
DEFAULT_IMAGE_ENGINE=fal
DEFAULT_VIDEO_ENGINE=fal-video
```

:::caution[Security Warning]
Never commit your `.env` file to version control. Use `.env.example` as a template.
:::

### 3. Start Services

```bash
docker-compose up -d
```

This starts:

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database |
| Backend | 8000 | FastAPI server |
| Frontend | 3000 | Next.js app |

### 4. Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│  :3000      │     │   :8000     │     │   :5432     │
└─────────────┘     └─────────────┘     └─────────────┘
    Next.js            FastAPI           postgres:16
```

---

## docker-compose.yml Reference

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: opensns
      POSTGRES_PASSWORD: opensns_password
      POSTGRES_DB: opensns
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U opensns"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://opensns:opensns_password@postgres:5432/opensns
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      API_KEY_ENCRYPTION_KEY: ${API_KEY_ENCRYPTION_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      FAL_KEY: ${FAL_KEY:-}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop but keep data
docker-compose down

# Stop and remove volumes (DELETES DATA)
docker-compose down -v
```

### Rebuild After Code Changes

```bash
docker-compose build
docker-compose up -d
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U opensns -d opensns

# Backup database
docker-compose exec postgres pg_dump -U opensns opensns > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U opensns -d opensns
```

---

## Configuration Options

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `API_KEY_ENCRYPTION_KEY` | Yes | AES key for API key encryption (32 chars) |
| `OPENAI_API_KEY` | No | OpenAI API key for LLM |
| `FAL_KEY` | No | Fal.ai API key for images/video |
| `DEFAULT_LLM_ENGINE` | No | `openai` or `ollama` (default: `mock`) |
| `DEFAULT_IMAGE_ENGINE` | No | `fal` or `comfyui` (default: `fal`) |
| `DEFAULT_VIDEO_ENGINE` | No | `fal-video` or `comfyui` (default: `fal-video`) |

### Custom Ports

Modify port mappings in `docker-compose.yml`:

```yaml
backend:
  ports:
    - "8080:8000"  # Host:Container

frontend:
  ports:
    - "80:3000"    # Serve on port 80
```

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
docker-compose logs backend

# Common issues:
# - Port already in use: Change port in docker-compose.yml
# - Database not ready: Wait for healthcheck or restart
```

### Database Connection Failed

```bash
# Check if postgres is healthy
docker-compose ps

# If postgres shows "unhealthy", restart it
docker-compose restart postgres
```

### Frontend Can't Reach Backend

Ensure `NEXT_PUBLIC_API_URL` matches your setup:

```yaml
frontend:
  environment:
    # Use docker service name for internal communication
    NEXT_PUBLIC_API_URL: http://backend:8000
    # Or use host machine address
    NEXT_PUBLIC_API_URL: http://host.docker.internal:8000
```

### Out of Memory

Increase Docker's memory limit in Docker Desktop settings, or reduce container resources.

---

## Next Steps

- [Production Deployment](/deployment/production) - HTTPS, security hardening
- [Configuration Guide](/getting-started/configuration) - All environment variables
- [API Reference](/api/authentication) - API documentation
