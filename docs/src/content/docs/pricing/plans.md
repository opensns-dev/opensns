---
title: Pricing & Plans
description: OpenSNS subscription tiers and credit-based pricing for hosted service
---

OpenSNS uses a simple credit-based pricing model. Self-hosted is always free and unlimited.

## Credit System

All AI generation consumes credits:

| Action | Credits |
|--------|---------|
| Image generation | 1 credit |
| Video generation | 12 credits |

## Plans Overview

| Feature | Free | Basic | Pro | Ultra |
|---------|------|-------|-----|-------|
| **Price** | $0/mo | $8.99/mo | $28.99/mo | $98.99/mo |
| **Credits/month** | 20 | 145 | 545 | 1,980 |
| **$/credit** | — | $0.062 | $0.053 | $0.050 |
| **Team members** | 1 | 1 | 3 | 20 |
| **API Access** | ❌ | ❌ | ✅ | ✅ |
| **Competitor Research** | ❌ | ✅ | ✅ | ✅ |
| **Priority Queue** | ❌ | ❌ | ✅ | ✅ |
| **White-label Export** | ❌ | ❌ | ❌ | ✅ |

**Higher tiers = better value per credit.**

### What Can You Generate?

| Plan | Images Only | Videos Only | Mixed (example) |
|------|-------------|-------------|-----------------|
| Free (20) | 20 images | 1 video | 8 images + 1 video |
| Basic (145) | 145 images | 12 videos | 85 images + 5 videos |
| Pro (545) | 545 images | 45 videos | 305 images + 20 videos |
| Ultra (1,980) | 1,980 images | 165 videos | 1,140 images + 70 videos |

## Self-Hosted (Unlimited)

OpenSNS is open-source under the MIT license. When you self-host, you have:

- **Unlimited credits** - No limits on generation
- **No subscription fees**
- **Full control over your data**
- **Customization freedom**

You only pay for the underlying AI APIs (OpenAI, Fal.ai, etc.) based on your actual usage.

```bash
git clone https://github.com/opensns-dev/opensns.git
cd opensns
docker-compose up -d
```

## Cloud Hosted Benefits

While self-hosting is free, our cloud-hosted service offers:

- **Zero infrastructure management** - We handle scaling, backups, and updates
- **Pre-configured AI integrations** - No API key setup required
- **Automatic updates** - Always on the latest version
- **Support** - Email/priority support based on plan

## Credit Usage

Your credits reset at the start of each billing cycle:

- **Image generation**: 1 credit per AI-generated image
- **Video generation**: 12 credits per AI-generated video

Exceeding your credit limit will prompt you to upgrade or wait for the next cycle. No surprise charges.

## API Access (Pro+)

Pro and Ultra plans include API access for:

- Programmatic campaign creation
- Bulk asset generation
- Integration with your existing tools
- Webhook notifications

See our [API documentation](/api) for details.

## Enterprise

Need more? Contact us for:

- Custom credit allocations
- SLA guarantees
- Dedicated infrastructure
- SSO/SAML integration
- Custom AI model fine-tuning

Email: enterprise@opensns.dev
