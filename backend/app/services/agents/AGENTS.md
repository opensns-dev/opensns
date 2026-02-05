# LANGGRAPH AGENTS MODULE

## OVERVIEW

LangGraph-based marketing workflow that orchestrates AI agents for product analysis, content generation, and verification.

## FILES

| File | Purpose |
|------|---------|
| `graph.py` | Workflow definition, `marketing_graph` instance, `run_marketing_workflow()` |
| `nodes.py` | Node implementations: research, strategy, generation, verification |
| `state.py` | `AgentState` TypedDict, data models (AdCopy, GeneratedAsset, etc.) |

## WORKFLOW

```
research → competitor_analysis → strategy
                                    │
                            ┌───────┴───────┐
                            │               │
              (requires_approval?)     (no approval needed)
                            ↓               ↓
                      [approval]      ┌─────┴─────┐
                            │         │           │
                            ↓         ↓           ↓
                    (resume) copy_generation  image_generation
                                   │              │
                                   │              ↓
                                   │      video_generation
                                   │              │
                                   └──────┬───────┘
                                          ↓
                                   merge_branches
                                          ↓
                                 platform_optimizer
                                          ↓
                               performance_predictor
                                          ↓
                                    verification
                                          │
                              ┌───────────┴───────────┐
                              ↓                       ↓
                     (passed or max retries)    (failed, retry)
                              ↓                       ↓
                             END              copy_generation
```

## KEY FUNCTIONS

### Entry Point
```python
from app.services.agents.graph import run_marketing_workflow

result = await run_marketing_workflow(
    campaign_id=1,
    user_id=1,
    product_url="https://...",
    user_config={"openai_api_key": "...", ...},
    requires_approval=False  # Set True to pause at approval node
)
```

### Engine Selection (in nodes.py)
- `_get_llm_engine(state)` - Returns configured LLM adapter
- `_get_image_engine(state)` - Returns image generation adapter
- `_get_video_engine(state)` - Returns video generation adapter

All use user config first, then fallback to system defaults.

## CONVENTIONS

### Node Function Signature
```python
async def node_name(state: AgentState) -> dict[str, Any]:
    # Process state
    # Return partial state update (merged automatically)
    return {
        "field_to_update": new_value,
        "current_step": "next_step",
    }
```

### Conditional Edges
```python
def route_function(state: AgentState) -> str | List[str]:
    if condition:
        return "node_a"
    return ["node_b", "node_c"]  # Parallel execution
```

### JSON Extraction
Use `_extract_json(text)` helper to parse LLM responses with markdown code blocks.

## STATE FIELDS

Key fields in `AgentState` (see `state.py` for full definition):
- `campaign_id`, `user_id`, `product_url` - Input context
- `product_context` - Scraped product info
- `angles` - Generated marketing angles
- `generated_copies`, `generated_images`, `generated_videos` - Outputs
- `requires_approval`, `is_approved` - Workflow control
- `retry_count`, `max_retries` - Verification retry logic

## ANTI-PATTERNS

- **NEVER** raise exceptions in nodes (return error in state instead)
- **NEVER** skip fallback generation when LLM/engine fails
- **NEVER** modify state directly (return updates only)

## EXTENDING

To add new node:
1. Define async function in `nodes.py` with `AgentState` param
2. Add to graph in `graph.py` via `workflow.add_node()`
3. Wire edges with `add_edge()` or `add_conditional_edges()`
