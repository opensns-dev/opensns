<p align="center">
  <img src="docs/src/assets/logo.svg" alt="OpenSNS" width="280" />
</p>

<p align="center">
  <strong>Open-Source AI Marketing Agent Platform</strong>
</p>

<p align="center">
  <a href="https://github.com/opensns-dev/opensns/actions"><img src="https://github.com/opensns-dev/opensns/workflows/CI/badge.svg" alt="CI"></a>
  <a href="https://github.com/opensns-dev/opensns/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://opensns-dev.github.io/opensns/"><img src="https://img.shields.io/badge/docs-online-green.svg" alt="Docs"></a>
</p>

<p align="center">
  Self-hostable AI marketing agent that generates ad creatives from a product URL.<br>
  100% open-source. Own your data. No vendor lock-in.
</p>

---

## ✨ Features

- **🔍 Product Analysis** — Scrapes and analyzes product pages to understand features and benefits
- **📊 Competitor Research** — AI-powered competitor analysis and differentiation strategy
- **🎯 Multi-Angle Strategy** — Generates multiple marketing angles for A/B testing
- **✍️ Ad Copy Generation** — Platform-specific ad copy (Instagram, Facebook, Google Ads, Naver)
- **🖼️ Image Generation** — AI-generated product images via Fal.ai or ComfyUI
- **🎬 Video Generation** — Image-to-video conversion for TikTok and Stories
- **📈 Performance Prediction** — AI-powered CTR and engagement predictions
- **📱 Multi-Platform Optimization** — Automatic resizing for each platform's specs

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI + SQLModel + LangGraph |
| **Frontend** | Next.js 15 (App Router) + shadcn/ui + Tailwind CSS |
| **Database** | PostgreSQL (SQLite for dev) |
| **LLM** | OpenAI / Ollama |
| **Image** | Fal.ai / ComfyUI |
| **Video** | Fal.ai / Runway / ComfyUI |

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
git clone https://github.com/opensns-dev/opensns.git
cd opensns

# Copy and configure environment
cp .env.example .env

# Generate required secrets (or set manually)
# JWT_SECRET_KEY and API_KEY_ENCRYPTION_KEY are required
# Generate with: openssl rand -hex 32

# Start all services
docker compose up -d

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

<details>
<summary><strong>Backend</strong></summary>

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your settings

uvicorn app.main:app --reload
```

</details>

<details>
<summary><strong>Frontend</strong></summary>

```bash
cd frontend
bun install
cp .env.example .env.local

bun dev
```

</details>

## 📖 Documentation

Full documentation is available at **[opensns-dev.github.io/opensns](https://opensns-dev.github.io/opensns/)**

- [Introduction](https://opensns-dev.github.io/opensns/getting-started/introduction/)
- [Quick Start Guide](https://opensns-dev.github.io/opensns/getting-started/quickstart/)
- [Configuration](https://opensns-dev.github.io/opensns/getting-started/configuration/)
- [Architecture Overview](https://opensns-dev.github.io/opensns/architecture/overview/)

## 🌐 Supported Platforms

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

## 🏗️ Architecture

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

## 🧪 Development

```bash
# Backend tests
cd backend && pytest -v

# Frontend tests
cd frontend && bun test

# E2E tests
cd frontend && bun e2e
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<p align="center">
  Made with ❤️ by the OpenSNS community
</p>
