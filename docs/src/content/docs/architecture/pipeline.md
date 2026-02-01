---
title: Agent Pipeline
description: LangGraph workflow for content generation
---

The agent pipeline is the core of OpenSNS. It orchestrates multiple AI agents to generate marketing assets.

## Pipeline Overview

```
START
  │
  ▼
┌─────────────────┐
│  Research Node  │  ← Scrapes product URL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Strategy Node  │  ← Generates marketing angles
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Copy Node     │  ← Creates ad copy
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Image │ │ Video │  ← Run in parallel
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│ Verification    │  ← Quality checks
└────────┬────────┘
         │
         ▼
       END
```

## Node Details

### Research Node

**Input**: Product URL  
**Output**: ProductInfo, images, metadata

```python
async def research_node(state: AgentState) -> AgentState:
    # 1. Scrape URL with Playwright
    product_info = await scraper.scrape_url(state.product_url)
    
    # 2. Extract key information
    state.product_title = product_info.title
    state.product_description = product_info.description
    state.product_images = product_info.images
    
    return state
```

### Strategy Node

**Input**: Product info  
**Output**: 3-5 marketing angles

Each angle includes:
- Name (e.g., "Premium Quality")
- Description
- Target audience
- Key messaging points

### Copy Node

**Input**: Angles, platforms  
**Output**: Ad copy for each combination

Generates:
- Headline
- Body copy
- Call-to-action
- Platform-specific formatting

### Image Node

**Input**: Product images, angles  
**Output**: Generated images

For each angle:
1. Fetch product image (scraped or generated)
2. Apply angle-specific prompt
3. Generate via Fal.ai / ComfyUI
4. Store result

### Video Node

**Input**: Generated images  
**Output**: Short-form videos

Converts images to video using:
- Fal.ai video generation
- Motion prompts based on angle
- Platform-optimized durations

### Verification Node

**Input**: All generated assets  
**Output**: Verification results

Checks:
- Image quality
- Copy coherence
- Platform compliance

## State Management

The pipeline uses `AgentState` to pass data between nodes:

```python
class AgentState(TypedDict):
    # Input
    campaign_id: int
    product_url: str
    
    # Research results
    product_title: str
    product_description: str
    product_images: List[str]
    
    # Strategy results
    marketing_angles: List[MarketingAngle]
    
    # Generated content
    generated_copies: List[AdCopy]
    generated_images: List[GeneratedAsset]
    generated_videos: List[GeneratedAsset]
    
    # Status
    error: Optional[str]
```

## Error Handling

Each node has fallback behavior:

| Node | Fallback |
|------|----------|
| Research | Basic HTTP → Fallback data |
| Strategy | Generic angles if LLM fails |
| Copy | Template-based copy |
| Image | Scraped product image |
| Video | Source image (no motion) |

## Parallel Execution

Image and video generation run in parallel when possible:

```python
graph.add_edge("copy_node", "image_node")
graph.add_edge("copy_node", "video_node")
graph.add_edge("image_node", "verification_node")
graph.add_edge("video_node", "verification_node")
```

## Checkpointing

LangGraph saves state after each node, enabling:
- Resume after interruption
- Debugging intermediate states
- Approval workflows
