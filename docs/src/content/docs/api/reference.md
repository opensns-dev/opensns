---
title: API Reference
description: Complete REST API endpoint reference for OpenSNS
---

For interactive API documentation, run the backend and visit `http://localhost:8000/docs`.

## Introduction

OpenSNS runs on FastAPI. Interactive API docs are available at `/docs` for Swagger UI and `/redoc` for ReDoc.

This page documents the REST routes that are currently defined in `backend/app/api/`. It stays aligned with the code, so if a route is not present in the backend it is not listed here.

## Authentication

Protected endpoints require this header:

```http
Authorization: Bearer <token>
```

The `/auth/login`, `/auth/refresh`, and `/auth/google/callback` routes return access and refresh tokens. Most authenticated routes use the JWT access token from `access_token`.

## Auth

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| POST | `/auth/register` | Create a new account with email and password | No | `email`, `password` | `id`, `email`, `is_active`, `is_verified`, `auth_provider`, `created_at` |
| POST | `/auth/verify?token=...` | Verify an email address with a verification token | No | `token` query parameter | `message` |
| POST | `/auth/resend-verification` | Send a new verification email | No | `email` | `message` |
| POST | `/auth/login` | Log in with email and password | No | OAuth2 form fields `username`, `password` | `access_token`, `token_type`, `refresh_token` |
| POST | `/auth/refresh` | Exchange a refresh token for a new access token | No | `refresh_token` | `access_token`, `token_type`, `refresh_token` |
| GET | `/auth/google` | Start Google OAuth login | No | None | `auth_url`, `state` |
| POST | `/auth/google/callback` | Complete Google OAuth login and create tokens | No | `code`, `state` | `access_token`, `token_type`, `refresh_token` |
| GET | `/auth/me` | Return the current user profile | Yes | None | `id`, `email`, `is_active`, `is_verified`, `auth_provider`, `created_at` |
| POST | `/auth/logout` | Clear the access cookie and revoke an optional refresh token | No | Optional `refresh_token` | `message` |

### Example login request

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secret"
```

### Example token response

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "refresh_token": "rft_123456789"
}
```

## Campaigns

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| POST | `/campaigns/` | Create a new campaign and start the generation pipeline | Yes | `title`, `product_url`, optional `description`, `brand_kit_id`, `template_id` | Campaign object with `id`, `title`, `product_url`, `status`, `created_at`, `updated_at` |
| GET | `/campaigns/` | List campaigns for the current user | Yes | None | Array of campaign objects |
| GET | `/campaigns/stats` | Return campaign counts by status | Yes | None | `total`, `completed`, `in_progress`, `failed` |
| GET | `/campaigns/{campaign_id}` | Get a single campaign by ID | Yes | `campaign_id` path parameter | Campaign object |
| POST | `/campaigns/{campaign_id}/approve` | Approve a campaign awaiting approval and resume processing | Yes | `campaign_id` path parameter | Campaign object |
| DELETE | `/campaigns/{campaign_id}` | Delete a campaign owned by the current user | Yes | `campaign_id` path parameter | `message` |
| GET | `/campaigns/{campaign_id}/export` | Export campaign assets as a ZIP file | Yes | `campaign_id` path parameter | ZIP download |

### Example create campaign request

```bash
curl -X POST http://localhost:8000/campaigns/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Spring launch",
    "product_url": "https://example.com/product",
    "description": "Generate ads for the spring campaign"
  }'
```

### Example campaign response

```json
{
  "id": 42,
  "title": "Spring launch",
  "product_url": "https://example.com/product",
  "description": "Generate ads for the spring campaign",
  "brand_kit_id": null,
  "template_id": null,
  "user_id": 7,
  "status": "PENDING",
  "created_at": "2026-04-13T09:00:00Z",
  "updated_at": "2026-04-13T09:00:00Z"
}
```

## Assets

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| GET | `/assets/campaign/{campaign_id}` | List assets for a campaign | No | `campaign_id` path parameter | Array of asset objects with `id`, `campaign_id`, `type`, `content`, `asset_metadata`, `ai_disclosure`, `created_at` |
| GET | `/assets/{asset_id}` | Get a single asset by ID | No | `asset_id` path parameter | Asset object |

### Example asset list request

```bash
curl http://localhost:8000/assets/campaign/42
```

### Example asset response

```json
[
  {
    "id": 301,
    "campaign_id": 42,
    "type": "IMAGE",
    "content": "https://cdn.example.com/assets/image.png",
    "asset_metadata": "{\"platform\":\"meta\",\"angle\":\"A\"}",
    "ai_disclosure": "{}",
    "created_at": "2026-04-13T09:10:00Z"
  }
]
```

## Settings

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| GET | `/settings/` | Get the current user settings record | Yes | None | Default engine settings, UGC settings, engine URLs, API key presence flags, AI label settings |
| PUT | `/settings/` | Update user settings, including API keys and engine URLs | Yes | Any subset of settings fields such as `default_llm_engine`, `openai_api_key`, `fal_api_key`, `ollama_url`, `ugc_enabled`, `ai_label_text` | Updated settings object |

### Example update settings request

```bash
curl -X PUT http://localhost:8000/settings/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "default_llm_engine": "openai",
    "ugc_enabled": true,
    "ai_label_text": "AI Generated"
  }'
```

### Example settings response

```json
{
  "default_llm_engine": "openai",
  "default_image_engine": "fal",
  "default_video_engine": "fal-video",
  "default_ugc_engine": "heygen",
  "ugc_enabled": true,
  "ugc_avatar_id": null,
  "ugc_voice_id": null,
  "ollama_url": null,
  "comfyui_url": null,
  "sadtalker_url": null,
  "default_tts_engine": "openai-tts",
  "default_bgm_engine": "static-bgm",
  "tts_enabled": false,
  "bgm_enabled": false,
  "tts_voice_id": null,
  "bgm_style": null,
  "has_openai_key": true,
  "has_fal_key": true,
  "has_firecrawl_key": false,
  "has_heygen_key": false,
  "has_did_key": false,
  "has_anthropic_key": false,
  "has_google_key": false,
  "has_groq_key": false,
  "ai_disclosure_enabled": true,
  "ai_label_text": "AI Generated",
  "ai_label_position": "BOTTOM_RIGHT"
}
```

## Billing

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| GET | `/billing/overview` | Return subscription, usage, and credit cost overview | Yes | None | `subscription`, `usage`, `credit_costs`, `usage_percentage` |
| GET | `/billing/plans` | List available subscription plans | No | None | Plan map keyed by tier |
| GET | `/billing/credit-packs` | List available credit packs | No | None | Credit pack map keyed by pack ID |
| GET | `/billing/ls-config` | Return LemonSqueezy configuration for the signed in user | Yes | None | `store_id`, `customer_email` |
| POST | `/billing/create-checkout` | Create a LemonSqueezy checkout URL | Yes | `variant_id`, optional `checkout_type`, optional `custom_data` | `url` |
| GET | `/billing/analytics?days=...` | Return credit usage analytics for the selected period | Yes | `days` query parameter | `period_days`, `total_credits`, `by_type`, `daily`, `lifetime` |
| POST | `/billing/webhook` | Internal LemonSqueezy webhook receiver | No | Signed webhook body, `X-Signature`, `X-Event-Name` headers | `status` |

### Example billing overview request

```bash
curl http://localhost:8000/billing/overview \
  -H "Authorization: Bearer <token>"
```

### Example billing overview response

```json
{
  "subscription": {
    "tier": "PRO",
    "status": "ACTIVE",
    "current_period_start": "2026-04-01T00:00:00Z",
    "current_period_end": "2026-05-01T00:00:00Z",
    "cancel_at_period_end": false,
    "limits": {
      "credits_per_month": 500,
      "team_members": 3
    }
  },
  "usage": {
    "period_start": "2026-04-01T00:00:00Z",
    "credits_used": 48,
    "credits_limit": 500,
    "bonus_credits": 0
  },
  "credit_costs": {
    "image": 1,
    "video": 12,
    "repurpose": 5,
    "product_photo": 3,
    "tts": 2,
    "bgm": 0
  },
  "usage_percentage": 9
}
```

## Publishing

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| GET | `/publishing/connections` | List active social publishing connections | Yes | None | Array of connection objects |
| DELETE | `/publishing/connections/{connection_id}` | Remove a publishing connection | Yes | `connection_id` path parameter | `message` |
| GET | `/publishing/meta/auth` | Start Meta OAuth flow | Yes | None | `auth_url`, `state` |
| GET | `/publishing/meta/callback?code=...&state=...` | Finish Meta OAuth flow and store page or Instagram connections | Yes | `code`, `state` | `connections` |
| GET | `/publishing/x/auth` | Start X OAuth flow | Yes | None | `auth_url`, `state` |
| GET | `/publishing/x/callback?code=...&state=...` | Finish X OAuth flow and store the connection | Yes | `code`, `state` | `connections` |
| GET | `/publishing/threads/auth` | Start Threads OAuth flow | Yes | None | `auth_url`, `state` |
| GET | `/publishing/threads/callback?code=...&state=...` | Finish Threads OAuth flow and store the connection | Yes | `code`, `state` | `connections` |
| POST | `/publishing/campaigns/{campaign_id}/publish` | Publish campaign assets to a selected social platform | Yes | `campaign_id` path parameter, `platform`, optional `asset_ids`, `caption`, `targeting`, `budget` | Publish log object |

### Example publish request

```bash
curl -X POST http://localhost:8000/publishing/campaigns/42/publish \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "FACEBOOK",
    "caption": "Spring launch",
    "asset_ids": [301]
  }'
```

### Example publish response

```json
{
  "id": 9001,
  "campaign_id": 42,
  "platform": "FACEBOOK",
  "status": "PUBLISHING",
  "external_post_id": null,
  "external_url": null,
  "error_message": null,
  "created_at": "2026-04-13T09:15:00Z"
}
```

## UGC

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| GET | `/ugc/engines` | List UGC engine availability for the current user | Yes | None | `engines`, `default_engine` |
| GET | `/ugc/avatars?engine=...` | List available avatars for a UGC engine | Yes | `engine` query parameter, default `heygen` | `avatars`, `engine` |
| GET | `/ugc/voices?engine=...` | List available voices for a UGC engine | Yes | `engine` query parameter, default `heygen` | `voices`, `engine` |

### Example UGC avatars request

```bash
curl http://localhost:8000/ugc/avatars?engine=heygen \
  -H "Authorization: Bearer <token>"
```

### Example UGC response

```json
{
  "engine": "heygen",
  "avatars": [
    {
      "avatar_id": "avatar_123",
      "name": "Professional Presenter"
    }
  ]
}
```

## Waitlist

| Method | Path | Description | Auth required | Key request fields | Key response fields |
| --- | --- | --- | --- | --- | --- |
| POST | `/waitlist/` | Join the waitlist | No | `email` | `id`, `email`, `source`, `created_at` |
| GET | `/waitlist/` | List waitlist entries | Yes | None | Array of waitlist entries |

### Example waitlist request

```bash
curl -X POST http://localhost:8000/waitlist/ \
  -H "Content-Type: application/json" \
  -d '{"email":"waitlist@example.com"}'
```

### Example waitlist response

```json
{
  "id": 12,
  "email": "waitlist@example.com",
  "source": "web",
  "created_at": "2026-04-13T09:20:00Z"
}
```

## Notes

Some route names in the product brief do not exist in the backend yet, so this page reflects the actual FastAPI routers instead of placeholder endpoints.

For exact request and response schemas, use the interactive Swagger UI or inspect the Pydantic models in `backend/app/models/models.py`.
