---
title: Web Scraping
description: How OpenSNS extracts product information
---

import { Aside } from '@astrojs/starlight/components';

OpenSNS uses a multi-layer scraping approach to extract product information from URLs.

## Scraping Pipeline

The scraper tries multiple methods in order:

1. **Playwright** (default) - Full browser rendering
2. **Firecrawl** (if configured) - Cloud-based scraping
3. **Basic HTTP** - Simple HTML fetching
4. **Fallback Data** - Minimal placeholder data

## Playwright Scraper

The primary scraper uses Playwright for full JavaScript rendering:

```python
# Handles:
- JavaScript-rendered content
- Dynamic loading
- Single Page Applications
- Anti-bot protections (via real browser)
```

### Extracted Data

| Field | Description |
|-------|-------------|
| `title` | Product name |
| `description` | Product description |
| `features` | Bullet points / feature list |
| `price` | Product price |
| `images` | Product image URLs |
| `content` | Main page text |
| `metadata` | Open Graph, JSON-LD data |

### Smart Selectors

The scraper uses multiple selector strategies:

```python
# Title selectors (tried in order)
"h1.product-title"
"h1.product-name"
"h1[itemprop='name']"
".product-title h1"
"#product-title"
"h1"
```

## Firecrawl Integration

For sites that block automation, Firecrawl provides cloud-based scraping:

1. Get API key from [firecrawl.dev](https://firecrawl.dev)
2. Add to Settings or environment
3. Scraper automatically uses it as fallback

<Aside type="tip">
Firecrawl is particularly useful for sites with aggressive bot protection.
</Aside>

## Handling Edge Cases

### JavaScript-Heavy Sites

Playwright waits for content to load:
- DOM content loaded
- Optional selector wait
- 1 second delay for dynamic content

### Anti-Bot Protection

The scraper uses realistic browser fingerprints:
- Real Chrome user agent
- Standard viewport size
- JavaScript enabled

### Rate Limiting

Be respectful of target sites:
- One request per campaign
- No rapid successive requests
- Respect robots.txt (manual check)

## Troubleshooting

### "Scraping failed" Error

1. Check if the URL is accessible in a browser
2. Try enabling Firecrawl
3. Check for CAPTCHA requirements
4. Verify URL is a product page (not homepage)

### Missing Product Data

Some sites don't expose structured data:
- Description in images only
- Dynamic pricing
- Login-required content

The scraper extracts what's available and uses AI to fill gaps.

## Best Practices

1. **Use direct product URLs** - Not category or search pages
2. **E-commerce platforms work best** - Shopify, WooCommerce, Amazon
3. **Public pages only** - Login-required pages won't work
4. **Check robots.txt** - Respect site policies
