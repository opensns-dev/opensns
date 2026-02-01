---
title: Creating Campaigns
description: How to create and manage marketing campaigns
---

import { Steps, Aside } from '@astrojs/starlight/components';

Campaigns are the core of OpenSNS. Each campaign takes a product URL and generates a complete set of marketing assets.

## Creating a Campaign

<Steps>

1. **Navigate to Campaigns**
   
   From the dashboard, click "Campaigns" in the sidebar or use the "Create Campaign" button.

2. **Enter campaign details**
   
   - **Title**: A name for your campaign (e.g., "Summer Collection Launch")
   - **Product URL**: The full URL of the product page to analyze

3. **Start generation**
   
   Click "Start Analysis" to begin the AI pipeline.

</Steps>

## Campaign Workflow

Once you create a campaign, it goes through these stages:

| Status | Description |
|--------|-------------|
| `PENDING` | Campaign created, waiting to start |
| `RESEARCHING` | AI is scraping and analyzing the product |
| `GENERATING` | Creating copy, images, and videos |
| `AWAITING_APPROVAL` | Assets ready for review |
| `COMPLETED` | Campaign finalized |
| `FAILED` | An error occurred |

## Real-time Progress

During `RESEARCHING` and `GENERATING` phases, you'll see live agent activity:

- Which agent is currently working
- What task is being performed
- Any errors or warnings

This uses WebSocket connections for instant updates.

## Reviewing Assets

Once generation completes, you can view:

### Images
- AI-generated product images
- Multiple angles and styles
- Platform-optimized sizes

### Videos
- Image-to-video conversions
- Short-form content for TikTok/Reels

### Ad Copy
- Platform-specific headlines
- Body copy with CTAs
- Multiple marketing angles

## Approving Assets

When status is `AWAITING_APPROVAL`:

1. Review all generated assets
2. Click "Approve & Launch Assets"
3. Campaign moves to `COMPLETED`

## Exporting Assets

Download all assets as a ZIP file:

1. Go to campaign detail page
2. Click "Export All"
3. ZIP includes:
   - All images (PNG)
   - All videos (MP4)
   - All copy (TXT)
   - Manifest with metadata

## Tips for Better Results

<Aside type="tip">
**Use detailed product pages**: Pages with good descriptions, features, and images produce better results.
</Aside>

- **Product URLs work best** - Homepage URLs have less focused content
- **E-commerce sites** - Amazon, Shopify stores work well
- **Include images** - Pages with product images enable better AI generation
