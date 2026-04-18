---
title: Engine Setup Guide
description: Configure AI engines for image, video, LLM, and UGC generation
---

OpenSNS uses a pluggable engine system. Each engine type, LLM, Image, Video, and UGC, can be swapped independently. You can set defaults globally with environment variables, then let individual users override them in the Settings UI when they add their own API keys.

## Overview

Engine configuration is split into two layers:

1. **Global defaults** from environment variables
2. **Per-user overrides** from **Settings > API Keys**

User-provided keys always take priority over global defaults. That makes it easy to run one shared deployment, while still letting power users bring their own provider accounts.

## LLM Engines

LLM engines power ad copy, strategy, research, and other text generation tasks.

### OpenAI

Recommended for production because it is the default, broadly supported, and easy to set up.

Required:

```bash
OPENAI_API_KEY=sk-your-key
```

Optional:

```bash
OPENAI_MODEL=gpt-4o
```

Set the default engine:

```bash
DEFAULT_LLM_ENGINE=openai
```

Notes:

- OpenSNS uses `OPENAI_BASE_URL` for OpenAI-compatible endpoints, and it defaults to `https://api.openai.com/v1`
- If you want the standard OpenAI API, you only need `OPENAI_API_KEY`

### Anthropic

Use Anthropic when you want Claude models for text generation.

Required:

```bash
ANTHROPIC_API_KEY=your-anthropic-key
```

Set the default engine:

```bash
DEFAULT_LLM_ENGINE=anthropic
```

Notes:

- Choose this when you want Claude-based copywriting or research
- Make sure the Anthropic key is configured globally or per user in Settings > API Keys

### Gemini

Use Google Gemini when you want Google’s LLMs for text generation.

Required:

```bash
GOOGLE_API_KEY=your-google-api-key
```

Set the default engine:

```bash
DEFAULT_LLM_ENGINE=gemini
```

Notes:

- This uses the `GOOGLE_API_KEY` setting from backend config
- Make sure your Google key is available before selecting Gemini as the default

### Groq

Use Groq when you want fast inference with supported open-source models.

Required:

```bash
GROQ_API_KEY=your-groq-key
```

Set the default engine:

```bash
DEFAULT_LLM_ENGINE=groq
```

Notes:

- This is a good option when speed matters more than model variety
- Make sure your Groq key is configured before switching the default engine

### Ollama

Good for self-hosted and local development setups.

Required:

- A running Ollama instance

Configure the endpoint and default engine:

```bash
OLLAMA_URL=http://localhost:11434
DEFAULT_LLM_ENGINE=ollama
```

Notes:

- Ollama is useful when you want to avoid external API usage
- Make sure the Ollama server is reachable from the OpenSNS backend

### Custom API

Use this option for any OpenAI-compatible provider, including Fireworks AI, Together AI, Groq-compatible gateways, and similar services.

Configure the shared OpenAI-style settings:

```bash
OPENAI_API_KEY=your-provider-key
OPENAI_BASE_URL=https://your-provider.example/v1
OPENAI_MODEL=your-model-name
DEFAULT_LLM_ENGINE=openai
```

Notes:

- Keep the `DEFAULT_LLM_ENGINE` set to `openai` when the provider follows the OpenAI API format
- Change only the base URL, key, and model name

## Image Engines

Image engines generate ad creative images.

### Fal.ai

Recommended cloud option for production.

Required:

```bash
FAL_KEY=your-fal-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=fal
```

Notes:

- Fal.ai supports image models such as Flux Dev and Flux Pro
- This is the easiest option if you want managed infrastructure and strong model quality

### Flux Pro

Use Flux Pro when you want another Fal.ai-backed image option with a stronger model tier.

Required:

```bash
FAL_KEY=your-fal-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=flux-pro
```

Notes:

- This uses the same Fal.ai key as the standard image engine
- Choose Flux Pro if you want to switch models without changing providers

### ComfyUI

Best for self-hosted deployments where you want full control over models and workflows.

Required:

- A running ComfyUI instance

Configure the endpoint and default engine:

```bash
COMFYUI_URL=http://localhost:8188
DEFAULT_IMAGE_ENGINE=comfyui
```

Notes:

- Install the appropriate Stable Diffusion or Flux models in your ComfyUI environment
- Make sure the backend can reach the ComfyUI server at the configured URL

### OpenRouter Image

Use OpenRouter when you already have an OpenRouter API key and want image generation via GPT Image or Nano Banana (Gemini Flash Image) models.

Required:

```bash
OPENROUTER_API_KEY=your-openrouter-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=openrouter-image
```

Notes:

- This uses the same API key as the OpenRouter LLM engine
- Supports GPT Image 1, Nano Banana (Gemini Flash Image), and other OpenRouter image models
- Good choice when you want a single API key for both LLM and image generation

### OpenAI GPT Image

Use OpenAI when you want GPT Image or DALL-E models directly from OpenAI.

Required:

```bash
OPENAI_API_KEY=sk-your-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=openai-image
```

Notes:

- This uses the same API key as the OpenAI LLM engine
- Supports GPT Image 1/1.5 and DALL-E 3

### Replicate

Use Replicate for access to FLUX, Stable Diffusion, and thousands of community image models.

Required:

```bash
REPLICATE_API_TOKEN=your-replicate-token
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=replicate
```

Notes:

- Replicate hosts a large catalog of open-source and commercial image models
- Generation is async with polling (handled automatically by the adapter)

### Together AI

Use Together AI for fast FLUX image generation.

Required:

```bash
TOGETHER_API_KEY=your-together-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=together
```

Notes:

- Supports FLUX.1 Schnell and FLUX.1 Pro models
- Good balance of speed and quality

### Stability AI

Use Stability AI for Stable Diffusion 3 and Stable Image generation.

Required:

```bash
STABILITY_API_KEY=your-stability-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=stability
```

Notes:

- Uses the Stable Image v2beta API
- Credit-based pricing

### Black Forest Labs (BFL)

Use BFL for FLUX Pro and FLUX Dev directly from the model creators.

Required:

```bash
BFL_API_KEY=your-bfl-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=bfl
```

Notes:

- Black Forest Labs created the FLUX model family
- Generation is async with polling (handled automatically)

### Leonardo AI

Use Leonardo AI for high-quality product and creative image generation.

Required:

```bash
LEONARDO_API_KEY=your-leonardo-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=leonardo
```

Notes:

- Offers specialized product photography and creative image models
- Generation is async with polling (handled automatically)

### Ideogram

Use Ideogram for images with strong text rendering and creative generation.

Required:

```bash
IDEOGRAM_API_KEY=your-ideogram-key
```

Set the default engine:

```bash
DEFAULT_IMAGE_ENGINE=ideogram
```

Notes:

- Strong at rendering text within images
- Good for ad creatives that need readable text overlays

## Video Engines

Video engines are used for image-to-video generation.

### Fal.ai Video

Recommended cloud option for production.

Required:

```bash
FAL_KEY=your-fal-key
```

Set the default engine:

```bash
DEFAULT_VIDEO_ENGINE=fal-video
```

Notes:

- This uses the same `FAL_KEY` as Fal.ai image generation
- It is the simplest choice if you already use Fal.ai for images

### Runway

Cloud video generation option for teams that already have Runway access.

Required:

- `FAL_KEY` for the Fal.ai-backed Runway adapter

Set the default engine:

```bash
DEFAULT_VIDEO_ENGINE=runway
```

Notes:

- Use this if you want a hosted video provider separate from your image stack
- This adapter is configured with the same `FAL_KEY` used for Fal.ai

### ComfyUI Video

Self-hosted option for image-to-video workflows, including AnimateDiff-based setups.

Required:

- A running ComfyUI instance with video-capable workflows and models

Configure the endpoint and default engine:

```bash
COMFYUI_URL=http://localhost:8188
DEFAULT_VIDEO_ENGINE=comfyui-video
```

Notes:

- This works best when your ComfyUI server already has the right motion models installed
- Use it if you want to keep generation fully local

## UGC Engines

UGC engines generate AI avatar talking-head videos.

### HeyGen

Recommended cloud option for production.

Required:

```bash
HEYGEN_API_KEY=your-heygen-key
```

Set the default engine:

```bash
DEFAULT_UGC_ENGINE=heygen
```

Notes:

- HeyGen supports custom avatars and multiple voices
- This is the strongest default choice if you want polished avatar output without self-hosting
- Pick this engine in Settings > API Keys for the user account that should use it

### D-ID

Cloud UGC option for teams already using D-ID.

Required:

```bash
DID_API_KEY=your-d-id-key
```

Set the default engine:

```bash
DEFAULT_UGC_ENGINE=d-id
```

Notes:

- Use this when you want a hosted avatar provider with a different pricing or workflow fit
- Make sure your API key is available to the backend
- Pick this engine in Settings > API Keys for the user account that should use it

### SadTalker

Self-hosted, free option for avatar talking-head generation.

Required:

- A running SadTalker instance

Configure the endpoint and default engine:

```bash
SADTALKER_URL=http://localhost:5000
```

Notes:

- Good for local or private deployments
- You are responsible for hosting and keeping the SadTalker service available
- In the current codebase, UGC engine selection is handled per user in Settings > API Keys rather than by a global default env var

## Object Storage

Object storage is required for production. There is no fallback for generated assets, so configure storage before running campaigns.

OpenSNS supports S3-compatible storage, including AWS S3, Cloudflare R2, and MinIO.

Required variables:

```bash
STORAGE_ENDPOINT_URL=https://your-storage-endpoint
STORAGE_ACCESS_KEY_ID=your-access-key
STORAGE_SECRET_ACCESS_KEY=your-secret-key
STORAGE_BUCKET_NAME=opensns-assets
STORAGE_PUBLIC_URL=https://your-public-bucket-url
```

Optional:

```bash
STORAGE_REGION=auto
```

### Cloudflare R2 example

```bash
STORAGE_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
STORAGE_ACCESS_KEY_ID=<r2-access-key>
STORAGE_SECRET_ACCESS_KEY=<r2-secret-key>
STORAGE_BUCKET_NAME=opensns-assets
STORAGE_PUBLIC_URL=https://pub-<bucket-id>.r2.dev
STORAGE_REGION=auto
```

### AWS S3 example

```bash
STORAGE_ENDPOINT_URL=https://s3.amazonaws.com
STORAGE_ACCESS_KEY_ID=<aws-access-key-id>
STORAGE_SECRET_ACCESS_KEY=<aws-secret-access-key>
STORAGE_BUCKET_NAME=opensns-assets
STORAGE_PUBLIC_URL=https://<bucket-name>.s3.amazonaws.com
STORAGE_REGION=us-east-1
```

### MinIO example

```bash
STORAGE_ENDPOINT_URL=http://localhost:9000
STORAGE_ACCESS_KEY_ID=minioadmin
STORAGE_SECRET_ACCESS_KEY=minioadmin
STORAGE_BUCKET_NAME=opensns-assets
STORAGE_PUBLIC_URL=http://localhost:9000/opensns-assets
STORAGE_REGION=us-east-1
```

## Per-User Configuration

Users can override the global defaults in **Settings > API Keys**.

When a user adds their own key, OpenSNS uses that provider for their account instead of the shared global key. This is useful for BYOK deployments, agency workspaces, and mixed-provider setups.

Typical setup:

- Global defaults provide the main production engines
- Individual users can swap to their own LLM, image, video, or UGC provider
- User-provided keys take priority over environment defaults

## Recommended Production Setup

| Engine Type | Recommended Provider | Why |
|-------------|----------------------|-----|
| LLM | OpenAI, Anthropic, Gemini, or Groq | Choose the provider that best matches your model quality, latency, and cost needs |
| Image | OpenRouter Image, Fal.ai, or OpenAI | OpenRouter shares a key with LLM; Fal.ai is simple cloud; OpenAI shares a key with LLM |
| Video | Fal.ai Video | Same key as image generation and a clean hosted workflow |
| UGC | HeyGen | Strong avatar and voice support for polished talking-head videos |
| Storage | Cloudflare R2 or AWS S3 | Durable, production-ready asset storage with S3 compatibility |

A practical production `.env` might look like this:

```bash
OPENROUTER_API_KEY=...
DEFAULT_LLM_ENGINE=openrouter
DEFAULT_IMAGE_ENGINE=openrouter-image
DEFAULT_VIDEO_ENGINE=fal-video

HEYGEN_API_KEY=...

STORAGE_ENDPOINT_URL=...
STORAGE_ACCESS_KEY_ID=...
STORAGE_SECRET_ACCESS_KEY=...
STORAGE_BUCKET_NAME=opensns-assets
STORAGE_PUBLIC_URL=...
```

For most teams, that combination gives the best balance of quality, setup speed, and operational simplicity.
