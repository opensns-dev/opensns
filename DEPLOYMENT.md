# OpenSNS Deployment Guide

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Cloudflare Pages│────▶│   Koyeb         │────▶│   Supabase      │
│ (Frontend+Docs) │     │   (Backend)     │     │   (PostgreSQL)  │
│ Next.js 16 SPA  │     │   FastAPI       │     │                 │
│ + Starlight     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │                       │
   Global CDN              Multi-region
   (Edge Network)     (FRA, WAS, SIN)
```

## Step 1: Supabase Setup

1. Go to https://supabase.com
2. Create New Project
   - Name: `opensns`
   - Region: `Singapore` (closest to Asia) or `US East`
   - Generate a strong database password and **save it**

3. Get Connection String:
   - Settings → Database → Connection string → URI
   - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

4. Enable Connection Pooling (recommended for serverless):
   - Settings → Database → Connection Pooling → Enable
   - Use the pooler connection string for `DATABASE_URL`

## Step 2: Koyeb Setup (Backend)

### Option A: Via Koyeb Dashboard (Recommended for first deploy)

1. Go to https://app.koyeb.com
2. Create App → Docker
3. Configure:
   - **Image**: `ghcr.io/opensns-dev/opensns-backend:latest`
   - **Port**: 8000
   - **Regions**: Frankfurt, Washington, Singapore
   - **Instance**: Nano ($2.68/month) or Micro ($5.36/month)

4. Environment Variables:
   ```
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
   JWT_SECRET_KEY=[generate with: openssl rand -hex 32]
   API_KEY_ENCRYPTION_KEY=[generate with: openssl rand -hex 32]
   FRONTEND_URL=https://opensns.pages.dev
   CORS_ORIGINS=https://opensns.pages.dev,http://localhost:3000
   OPENAI_API_KEY=[your key]
   FAL_KEY=[your key]
   PADDLE_API_KEY=[your key]
   PADDLE_WEBHOOK_SECRET=[your secret]
   PADDLE_ENVIRONMENT=production
   RESEND_API_KEY=[your key]
   GOOGLE_CLIENT_ID=[your id]
   GOOGLE_CLIENT_SECRET=[your secret]
   ```

5. Health Check:
   - Path: `/health`
   - Port: 8000

6. Deploy!

### Option B: Via GitHub Actions (for subsequent deploys)

1. Get Koyeb API Token:
   - Account Settings → API → Create Token

2. Add GitHub Secret:
   - Repository → Settings → Secrets → Actions
   - Name: `KOYEB_TOKEN`
   - Value: [your token]

3. Push to main branch triggers auto-deploy

## Step 3: Cloudflare Pages Setup (Frontend + Docs)

1. Go to https://dash.cloudflare.com
2. Workers & Pages → Create application → Pages → Connect to Git
3. Select repository: `opensns-dev/opensns`
4. Configure:
   - **Project name**: `opensns`
   - **Production branch**: `main`
   - **Root directory**: `/` (project root)
   - **Build command**: `npm run build`
   - **Build output directory**: `frontend/out`

5. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://opensns-backend-[your-id].koyeb.app
   NEXT_PUBLIC_WS_URL=wss://opensns-backend-[your-id].koyeb.app
   ```

6. Deploy!

**Your URLs:**
- App: `https://opensns.pages.dev/`
- Docs: `https://opensns.pages.dev/docs/`

## Step 4: Update Backend CORS

After Cloudflare Pages deploy, update Koyeb environment:
```
FRONTEND_URL=https://opensns.pages.dev
CORS_ORIGINS=https://opensns.pages.dev
```

## Step 5: Domain Setup (Optional)

### Custom Domain for Cloudflare Pages
1. Workers & Pages → opensns → Custom domains
2. Add your domain (e.g., `opensns.io`)
3. Cloudflare handles DNS automatically if domain is on Cloudflare

### Custom Domain for Backend (Koyeb)
1. Koyeb → App → Settings → Domains
2. Add subdomain (e.g., `api.opensns.io`)
3. Update DNS CNAME to Koyeb endpoint

### Update Environment Variables
After custom domains:
```
# Backend
FRONTEND_URL=https://opensns.io
CORS_ORIGINS=https://opensns.io

# Frontend (Cloudflare Pages)
NEXT_PUBLIC_API_URL=https://api.opensns.io
NEXT_PUBLIC_WS_URL=wss://api.opensns.io
```

## Estimated Monthly Cost

| Service | Plan | Cost |
|---------|------|------|
| Supabase | Free (500MB) | $0 |
| Koyeb | Nano x3 regions | ~$8 |
| Cloudflare Pages | Free (unlimited) | $0 |
| **Total** | | **~$8/month** |

For higher traffic:
| Service | Plan | Cost |
|---------|------|------|
| Supabase | Pro (8GB) | $25 |
| Koyeb | Micro x3 regions | ~$16 |
| Cloudflare Pages | Free (unlimited) | $0 |
| **Total** | | **~$41/month** |

## Local Development

```bash
# Build everything locally
npm run build

# Output structure:
# frontend/out/        → Next.js static site
# frontend/out/docs/   → Starlight docs
```

## Troubleshooting

### Database Connection Issues
- Ensure Supabase allows connections from Koyeb IPs
- Use connection pooling for serverless environments
- Check SSL mode: `?sslmode=require`

### CORS Errors
- Verify `CORS_ORIGINS` includes your frontend URL
- Check for trailing slashes (don't include them)

### WebSocket Issues
- Koyeb supports WebSocket natively
- Ensure `NEXT_PUBLIC_WS_URL` uses `wss://` protocol

### Health Check Failures
- Verify `/health` endpoint returns 200
- Check container startup time (may need to increase timeout)

### SPA Routing (404 on refresh)
- Cloudflare Pages handles SPA routing via `_redirects` file
- Already configured in `frontend/public/_redirects`
