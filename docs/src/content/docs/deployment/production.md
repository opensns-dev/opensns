---
title: Production Deployment
description: Deploy OpenSNS to production with security best practices
---

This guide covers deploying OpenSNS to a production environment with proper security, HTTPS, and monitoring.

## Production Checklist

Before going live, ensure:

- [ ] Strong, unique secrets for `JWT_SECRET_KEY` and `API_KEY_ENCRYPTION_KEY`
- [ ] HTTPS configured with valid SSL certificates
- [ ] Database backups configured
- [ ] Rate limiting enabled (built-in)
- [ ] CORS configured for your domain
- [ ] Monitoring and logging set up

---

## Deployment Options

### Option 1: VPS with Docker Compose

Best for: Small to medium deployments, full control

**Recommended providers:** DigitalOcean, Linode, Vultr, Hetzner

```bash
# On your VPS
git clone https://github.com/yourusername/opensns.git
cd opensns

# Create production environment file
cp .env.example .env
# Edit .env with production values
```

### Option 2: Container Platform

Best for: Scaling, managed infrastructure

**Recommended platforms:**
- Railway
- Render
- Fly.io
- Google Cloud Run
- AWS ECS

### Option 3: Kubernetes

Best for: Large scale, complex requirements

See the [Kubernetes section](#kubernetes-deployment) below.

---

## Security Configuration

### Generate Strong Secrets

```bash
# Generate JWT secret (64 characters)
openssl rand -base64 48

# Generate encryption key (exactly 32 characters for AES-256)
openssl rand -base64 24 | head -c 32
```

### Production Environment Variables

```bash
# .env.production
NODE_ENV=production

# Security (REQUIRED - use your generated values)
JWT_SECRET_KEY=<your-64-char-random-string>
API_KEY_ENCRYPTION_KEY=<your-32-char-random-string>

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/opensns

# CORS - restrict to your domain
CORS_ORIGINS=["https://yourdomain.com"]

# API Keys (optional - users can add their own)
OPENAI_API_KEY=
FAL_KEY=

# Engines
DEFAULT_LLM_ENGINE=openai
DEFAULT_IMAGE_ENGINE=fal
DEFAULT_VIDEO_ENGINE=fal-video
```

### Database Security

1. **Use a managed database** (AWS RDS, DigitalOcean Managed Database, etc.)
2. **Enable SSL connections**
3. **Use strong, unique passwords**
4. **Restrict network access** to only your application servers

```bash
# Example: PostgreSQL with SSL
DATABASE_URL=postgresql://user:pass@host:5432/opensns?sslmode=require
```

---

## HTTPS with Nginx

### Install Nginx and Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### Nginx Configuration

Create `/etc/nginx/sites-available/opensns`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # 5 min for asset generation
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Enable and Get SSL Certificate

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/opensns /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Reload Nginx
sudo systemctl reload nginx
```

---

## Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      DATABASE_URL: ${DATABASE_URL}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      API_KEY_ENCRYPTION_KEY: ${API_KEY_ENCRYPTION_KEY}
      CORS_ORIGINS: '["https://yourdomain.com"]'
    ports:
      - "127.0.0.1:8000:8000"  # Only localhost
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: https://yourdomain.com/api
    restart: always
    ports:
      - "127.0.0.1:3000:3000"  # Only localhost
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Start with:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Database Backups

### Automated Backups with Cron

Create `/opt/opensns/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/opensns/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/opensns_$TIMESTAMP.sql.gz"

# Create backup
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
```

Add to crontab:

```bash
# Run daily at 3 AM
0 3 * * * /opt/opensns/backup.sh >> /var/log/opensns-backup.log 2>&1
```

### Offsite Backups

Upload to S3 or similar:

```bash
# Install AWS CLI
pip install awscli

# Add to backup script
aws s3 cp "$BACKUP_FILE" "s3://your-bucket/opensns-backups/"
```

---

## Monitoring

### Health Checks

The backend exposes a health endpoint:

```bash
curl https://yourdomain.com/api/health
```

### Uptime Monitoring

Use services like:
- [UptimeRobot](https://uptimerobot.com/) (free)
- [Better Uptime](https://betteruptime.com/)
- [Pingdom](https://www.pingdom.com/)

Configure to check:
- `https://yourdomain.com` (frontend)
- `https://yourdomain.com/api/health` (backend)

### Log Aggregation

```bash
# View logs
docker-compose logs -f --tail=100

# Ship to external service (example: Papertrail)
# Add to docker-compose.prod.yml:
logging:
  driver: syslog
  options:
    syslog-address: "udp://logs.papertrailapp.com:12345"
```

---

## Kubernetes Deployment

For Kubernetes, create the following manifests:

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: opensns
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: opensns-secrets
  namespace: opensns
type: Opaque
stringData:
  jwt-secret-key: "your-jwt-secret"
  api-key-encryption-key: "your-encryption-key"
  database-url: "postgresql://..."
```

### Backend Deployment

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: opensns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/opensns-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: opensns-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: opensns-secrets
              key: jwt-secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

---

## Scaling Considerations

### Horizontal Scaling

- Backend is stateless - scale with multiple replicas
- Use a load balancer (Nginx, HAProxy, cloud LB)
- Ensure database can handle connection pooling

### Caching

Add Redis for session caching and rate limiting:

```yaml
# docker-compose.prod.yml
redis:
  image: redis:7-alpine
  restart: always
  ports:
    - "127.0.0.1:6379:6379"
```

### CDN for Assets

Store generated images/videos on a CDN:
- AWS S3 + CloudFront
- Cloudflare R2
- DigitalOcean Spaces

---

## Troubleshooting

### 502 Bad Gateway

Backend not responding:
```bash
docker-compose logs backend
docker-compose restart backend
```

### Database Connection Issues

```bash
# Test database connection
docker-compose exec backend python -c "from app.db import engine; print(engine.url)"
```

### SSL Certificate Renewal

Certbot auto-renews, but verify:
```bash
sudo certbot renew --dry-run
```

---

## Next Steps

- Set up [monitoring dashboards](/deployment/monitoring) (coming soon)
- Configure [CI/CD pipelines](/deployment/ci-cd) (coming soon)
- Review [security hardening](/deployment/security) (coming soon)
