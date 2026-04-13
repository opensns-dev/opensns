from typing import Callable, Awaitable

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.services.agents.state import AgentState
from app.services.agents.nodes import (
    research_node,
    competitor_analysis_node,
    strategy_node,
    copy_generation_node,
    image_generation_node,
    video_generation_node,
    ugc_video_generation_node,
    tts_generation_node,
    bgm_generation_node,
    audio_mixing_node,
    platform_optimizer_node,
    performance_predictor_node,
    verification_node,
    should_retry,
    route_after_strategy,
    merge_parallel_branches,
)


def build_marketing_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("research", research_node)
    workflow.add_node("competitor_analysis", competitor_analysis_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("approval", lambda x: x)  # Barrier node for approval
    workflow.add_node("copy_generation", copy_generation_node)
    workflow.add_node("image_generation", image_generation_node)
    workflow.add_node("video_generation", video_generation_node)
    workflow.add_node("ugc_video_generation", ugc_video_generation_node)
    workflow.add_node("tts_generation", tts_generation_node)
    workflow.add_node("bgm_generation", bgm_generation_node)
    workflow.add_node("audio_mixing", audio_mixing_node)
    workflow.add_node("merge_branches", merge_parallel_branches)
    workflow.add_node("platform_optimizer", platform_optimizer_node)
    workflow.add_node("performance_predictor", performance_predictor_node)
    workflow.add_node("verification", verification_node)

    workflow.set_entry_point("research")

    workflow.add_edge("research", "competitor_analysis")
    workflow.add_edge("competitor_analysis", "strategy")

    workflow.add_conditional_edges(
        "strategy",
        route_after_strategy,
        {
            "copy_generation": "copy_generation",
            "image_generation": "image_generation",
            "approval": "approval",
        },
    )

    # From approval, we re-evaluate where to go.
    # If approved, it will go to generation nodes.
    workflow.add_conditional_edges(
        "approval",
        route_after_strategy,
        {
            "copy_generation": "copy_generation",
            "image_generation": "image_generation",
            "approval": "approval",
        },
    )

    workflow.add_edge("copy_generation", "tts_generation")
    workflow.add_edge("tts_generation", "ugc_video_generation")
    workflow.add_edge("ugc_video_generation", "audio_mixing")
    workflow.add_edge("image_generation", "video_generation")
    workflow.add_edge("video_generation", "bgm_generation")
    workflow.add_edge("bgm_generation", "audio_mixing")
    workflow.add_edge("audio_mixing", "merge_branches")
    # ...

    workflow.add_edge("merge_branches", "platform_optimizer")
    workflow.add_edge("platform_optimizer", "performance_predictor")
    workflow.add_edge("performance_predictor", "verification")

    workflow.add_conditional_edges(
        "verification",
        should_retry,
        {
            "complete": END,
            "retry": "copy_generation",
        },
    )

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["approval"],
    )


marketing_graph = build_marketing_graph()


async def run_marketing_workflow(
    campaign_id: int,
    user_id: int,
    product_url: str,
    user_config: dict,
    requires_approval: bool = False,
    brand_kit: dict | None = None,
    on_step_change: Callable[[str], Awaitable[None]] | None = None,
) -> AgentState:
    initial_state: AgentState = {
        "campaign_id": campaign_id,
        "user_id": user_id,
        "product_url": product_url,
        "product_context": "",
        "openai_api_key": user_config.get("openai_api_key"),
        "fal_api_key": user_config.get("fal_api_key"),
        "firecrawl_api_key": user_config.get("firecrawl_api_key"),
        "ollama_url": user_config.get("ollama_url"),
        "comfyui_url": user_config.get("comfyui_url"),
        "heygen_api_key": user_config.get("heygen_api_key"),
        "did_api_key": user_config.get("did_api_key"),
        "default_llm_engine": user_config.get("default_llm_engine"),
        "default_image_engine": user_config.get("default_image_engine"),
        "default_video_engine": user_config.get("default_video_engine"),
        "default_ugc_engine": user_config.get("default_ugc_engine"),
        "ugc_enabled": user_config.get("ugc_enabled", False),
        "ugc_avatar_id": user_config.get("ugc_avatar_id"),
        "ugc_voice_id": user_config.get("ugc_voice_id"),
        # Audio configuration
        "elevenlabs_api_key": user_config.get("elevenlabs_api_key"),
        "default_tts_engine": user_config.get("default_tts_engine"),
        "default_bgm_engine": user_config.get("default_bgm_engine"),
        "tts_voice_id": user_config.get("tts_voice_id"),
        "bgm_style": user_config.get("bgm_style"),
        "tts_enabled": user_config.get("tts_enabled", False),
        "bgm_enabled": user_config.get("bgm_enabled", False),
        "brand_kit": brand_kit,
        "research_data": None,
        "competitor_insights": [],
        "angles": [],
        "generated_copies": [],
        "generated_images": [],
        "generated_videos": [],
        "generated_ugc_videos": [],
        # Audio pipeline outputs
        "generated_tts": [],
        "generated_bgm": [],
        "mixed_videos": [],
        "mixed_ugc_videos": [],
        "optimized_assets": [],
        "performance_predictions": [],
        "verification_results": [],
        "verification_feedback": None,
        "failed_items": [],
        "current_step": "research",
        "retry_count": 0,
        "max_retries": 2,
        "error": None,
        "is_complete": False,
        "copy_done": False,
        "visual_done": False,
        "ugc_done": False,
        "tts_done": False,
        "bgm_done": False,
        "audio_mixed": False,
        "requires_approval": requires_approval,
        "is_approved": not requires_approval,
    }

    config = {"configurable": {"thread_id": str(campaign_id)}}

    if on_step_change:
        async for event in marketing_graph.astream(initial_state, config=config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    step = node_output.get("current_step")
                    if step:
                        await on_step_change(step)
        return marketing_graph.get_state(config).values

    final_state = await marketing_graph.ainvoke(initial_state, config=config)
    return final_state


async def resume_after_approval(campaign_id: int) -> AgentState:
    config = {"configurable": {"thread_id": str(campaign_id)}}
    # Update state to mark as approved
    await marketing_graph.aupdate_state(config, {"is_approved": True})
    # Resume from the last checkpoint
    # Since it reached END after strategy, we might need to kick it back to a node
    # or ensure strategy points somewhere other than END when approval is needed.
    return await marketing_graph.ainvoke(None, config=config)
