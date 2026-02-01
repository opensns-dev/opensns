# OpenSNS - Open-Source AI Marketing Agent Platform

An open-source AI marketing agent that generates ad creatives from a product URL. Similar to Zet AI but fully open-source.

## Features

- **Product Analysis**: Scrapes and analyzes product pages to understand features and benefits
- **Competitor Research**: AI-powered competitor analysis and differentiation strategy
- **Multi-Angle Strategy**: Generates multiple marketing angles for A/B testing
- **Ad Copy Generation**: Platform-specific ad copy (Instagram, Facebook, Google Ads, Naver)
- **Image Generation**: AI-generated product images via Fal.ai or ComfyUI
- **Video Generation**: Image-to-video conversion for TikTok and Stories
- **Performance Prediction**: AI-powered CTR and engagement predictions
- **Multi-Platform Optimization**: Automatic resizing for each platform's specs

## Tech Stack

- **Backend**: FastAPI + SQLModel + LangGraph
- **Frontend**: Next.js 15 (App Router) + shadcn/ui + Tailwind CSS
- **Database**: PostgreSQL (SQLite for dev)
- **AI Engines**:
  - LLM: OpenAI / Ollama
  - Image: Fal.ai / ComfyUI
  - Video: Fal.ai / Runway / ComfyUI

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/opensns.git
cd opensns

# Copy environment files
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose up -d

# Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
bun install

# Copy and configure environment
cp .env.example .env.local
# Edit .env.local if needed

# Run development server
bun dev
```

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./opensns.db` |
| `JWT_SECRET_KEY` | Secret for JWT tokens (min 32 chars) | Required |
| `API_KEY_ENCRYPTION_KEY` | Key for encrypting stored API keys | Required |
| `OPENAI_API_KEY` | OpenAI API key for LLM | Optional |
| `FAL_KEY` | Fal.ai API key for image/video | Optional |
| `DEFAULT_LLM_ENGINE` | Default LLM engine | `openai` |
| `DEFAULT_IMAGE_ENGINE` | Default image engine | `fal` |
| `DEFAULT_VIDEO_ENGINE` | Default video engine | `fal-video` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (OAuth2 form)
- `GET /auth/me` - Get current user

### Campaigns
- `GET /campaigns` - List user's campaigns
- `POST /campaigns` - Create new campaign
- `GET /campaigns/{id}` - Get campaign details

### Settings
- `GET /settings` - Get user settings
- `PUT /settings` - Update settings
- `POST /settings/test-connection` - Test API key connectivity

### Assets
- `GET /assets` - List generated assets
- `GET /assets/{id}` - Get asset details

## Supported Platforms

### Global
- Instagram (Feed, Story)
- Facebook (Feed)
- Google Ads (Display)
- TikTok

### Korea (Naver)
- Naver Search Ads (PowerLink, Brand Search)
- Naver GFA (Native Feed, Banners)
- Naver Shopping (Product, Brand Zone)
- Naver TV/Shorts (Video)
- Naver Blog/Cafe (Content Marketing)

## Architecture

```
┌──────────────────┐     ┌──────────────────┐
│   Next.js 15     │────▶│    FastAPI       │
│   (Frontend)     │◀────│    (Backend)     │
└──────────────────┘     └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │   LangGraph      │
                         │   Workflow       │
                         └────────┬─────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐       ┌────────▼────────┐       ┌────────▼────────┐
│  LLM Engine   │       │  Image Engine   │       │  Video Engine   │
│  OpenAI/Ollama│       │  Fal/ComfyUI    │       │  Fal/Runway     │
└───────────────┘       └─────────────────┘       └─────────────────┘
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
bun test
```

### Project Structure

```
opensns/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, auth, utils
│   │   ├── models/       # SQLModel models
│   │   └── services/     # Business logic
│   │       └── agents/   # LangGraph workflow
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # Utilities
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.
