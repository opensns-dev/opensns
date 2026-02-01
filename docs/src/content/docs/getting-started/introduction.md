---
title: Introduction
description: What is OpenSNS and why use it
---

OpenSNS is an open-source AI marketing platform that automatically generates ad creatives from product URLs. It's designed for marketers, e-commerce businesses, and agencies who need to create high-quality marketing assets at scale.

## What Does OpenSNS Do?

Given a product URL, OpenSNS:

1. **Scrapes the product page** using Playwright (handles JavaScript-rendered content)
2. **Analyzes the product** to understand features, benefits, and target audience
3. **Generates marketing angles** for different messaging approaches
4. **Creates ad copy** optimized for each platform (Instagram, Facebook, Google Ads, Naver)
5. **Generates images** using AI (Fal.ai or ComfyUI)
6. **Creates videos** from images for TikTok, Reels, and Stories

## Key Features

### Multi-Platform Support

OpenSNS generates assets optimized for:

| Platform | Asset Types |
|----------|-------------|
| Instagram | Feed (1:1), Stories (9:16) |
| Facebook | Feed (1.91:1) |
| Google Ads | Display (1.91:1, 1:1) |
| TikTok | Video (9:16) |
| Naver | PowerLink, GFA, Shopping |

### Flexible AI Backends

Choose your preferred AI providers:

- **LLM**: OpenAI GPT-4 or local Ollama
- **Images**: Fal.ai (cloud) or ComfyUI (local)
- **Videos**: Fal.ai or Runway

### Real-time Progress

Watch the AI agents work in real-time with WebSocket-powered live updates.

## Architecture Overview

```
┌──────────────────┐     ┌──────────────────┐
│   Next.js 15     │────▶│    FastAPI       │
│   (Frontend)     │◀────│    (Backend)     │
└──────────────────┘     └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │   LangGraph      │
                         │   Agent Pipeline │
                         └────────┬─────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐       ┌────────▼────────┐       ┌────────▼────────┐
│  LLM Engine   │       │  Image Engine   │       │  Video Engine   │
│  OpenAI/Ollama│       │  Fal/ComfyUI    │       │  Fal/Runway     │
└───────────────┘       └─────────────────┘       └─────────────────┘
```

## Who Is This For?

- **Marketers** who need to create ads at scale
- **E-commerce businesses** launching new products
- **Agencies** managing multiple client campaigns
- **Developers** who want to customize the AI pipeline

## Open Source

OpenSNS is MIT licensed. You can:

- Self-host on your own infrastructure
- Customize the AI prompts and workflows
- Add new platforms and engines
- Contribute to the project

Ready to get started? Check out the [Quick Start guide](/getting-started/quickstart/).
