import json
from app.models.models import (
    Campaign,
    CampaignStatus,
    AgentLog,
    Asset,
    AssetType,
    UserSettings,
    User,
)
from app.db import engine
from sqlmodel import Session
from app.services.agents.graph import run_marketing_workflow, resume_after_approval
from app.services.agents.state import AgentState
from app.api.websocket import send_agent_log
from app.core.encryption import decrypt_api_key
from app.core.config import settings as app_settings


def _get_user_api_config(session: Session, user_id: int) -> dict:
    """Fetch and decrypt user's API configuration."""
    user_settings = session.get(UserSettings, user_id)

    if not user_settings:
        return {
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
        }

    openai_key = None
    if user_settings.openai_api_key:
        try:
            openai_key = decrypt_api_key(
                user_settings.openai_api_key,
                app_settings.API_KEY_ENCRYPTION_KEY,
            )
        except Exception:
            pass

    fal_key = None
    if user_settings.fal_api_key:
        try:
            fal_key = decrypt_api_key(
                user_settings.fal_api_key,
                app_settings.API_KEY_ENCRYPTION_KEY,
            )
        except Exception:
            pass

    firecrawl_key = None
    if user_settings.firecrawl_api_key:
        try:
            firecrawl_key = decrypt_api_key(
                user_settings.firecrawl_api_key,
                app_settings.API_KEY_ENCRYPTION_KEY,
            )
        except Exception:
            pass

    return {
        "openai_api_key": openai_key,
        "fal_api_key": fal_key,
        "firecrawl_api_key": firecrawl_key,
        "ollama_url": user_settings.ollama_url,
        "comfyui_url": user_settings.comfyui_url,
        "default_llm_engine": user_settings.default_llm_engine,
        "default_image_engine": user_settings.default_image_engine,
        "default_video_engine": user_settings.default_video_engine,
    }


async def _log_and_broadcast(
    session: Session,
    campaign_id: int,
    agent_name: str,
    message: str,
    level: str = "INFO",
):
    session.add(
        AgentLog(
            campaign_id=campaign_id,
            agent_name=agent_name,
            message=message,
            level=level,
        )
    )
    session.commit()
    await send_agent_log(campaign_id, agent_name, message, level)


async def run_campaign_pipeline(campaign_id: int, requires_approval: bool = False):
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            return

        product_url = campaign.product_url
        user_id = campaign.user_id

        user_config = _get_user_api_config(session, user_id)

        campaign.status = CampaignStatus.RESEARCHING
        session.add(campaign)
        session.commit()

        await _log_and_broadcast(
            session, campaign_id, "System", "Starting marketing workflow"
        )

    try:
        final_state = await run_marketing_workflow(
            campaign_id=campaign_id,
            user_id=user_id,
            product_url=product_url,
            user_config=user_config,
            requires_approval=requires_approval,
        )
    except Exception as e:
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign:
                campaign.status = CampaignStatus.FAILED
                session.add(campaign)
                session.commit()
            await _log_and_broadcast(
                session, campaign_id, "System", f"Workflow error: {e}", "ERROR"
            )
        raise

    if final_state.get("current_step") == "awaiting_approval":
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign:
                campaign.status = CampaignStatus.AWAITING_APPROVAL
                session.add(campaign)
                session.commit()
            await _log_and_broadcast(
                session,
                campaign_id,
                "System",
                "Workflow paused. Awaiting approval.",
            )
        return final_state

    await _save_final_state(campaign_id, final_state)
    return final_state


async def approve_and_resume(campaign_id: int):
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if campaign:
            campaign.status = CampaignStatus.RESEARCHING
            session.add(campaign)
            session.commit()
        await _log_and_broadcast(
            session, campaign_id, "System", "Approval received. Resuming workflow."
        )

    try:
        final_state = await resume_after_approval(campaign_id)
    except Exception as e:
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign:
                campaign.status = CampaignStatus.FAILED
                session.add(campaign)
                session.commit()
            await _log_and_broadcast(
                session, campaign_id, "System", f"Resume error: {e}", "ERROR"
            )
        raise

    await _save_final_state(campaign_id, final_state)
    return final_state


async def _save_final_state(campaign_id: int, final_state: AgentState):
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            return

        user = session.get(User, campaign.user_id)

        for copy in final_state.get("generated_copies", []):
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.COPY,
                content=f"{copy.headline}\n\n{copy.body}\n\n{copy.cta}",
                asset_metadata=json.dumps({"platform": copy.platform}),
            )
            session.add(asset)

        generated_images = final_state.get("generated_images", [])
        for image in generated_images:
            is_fallback = image.metadata.get("fallback", False)
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.IMAGE,
                content=image.content,
                asset_metadata=json.dumps(image.metadata),
            )
            session.add(asset)

        generated_videos = final_state.get("generated_videos", [])
        for video in generated_videos:
            is_fallback = video.metadata.get("fallback", False)
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.VIDEO,
                content=video.content,
                asset_metadata=json.dumps(video.metadata),
            )
            session.add(asset)

        if user:
            from app.services.usage import use_image_credits, use_video_credits

            real_images = [
                img
                for img in generated_images
                if not img.metadata.get("fallback", False)
            ]
            real_videos = [
                vid
                for vid in generated_videos
                if not vid.metadata.get("fallback", False)
            ]
            if real_images:
                use_image_credits(session, user, len(real_images))
            if real_videos:
                use_video_credits(session, user, len(real_videos))

        for optimized in final_state.get("optimized_assets", []):
            asset_type = (
                AssetType.IMAGE if optimized.asset_type == "image" else AssetType.VIDEO
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=asset_type,
                content=optimized.content,
                asset_metadata=json.dumps(
                    {
                        **optimized.metadata,
                        "platform_optimized": True,
                    }
                ),
            )
            session.add(asset)

        if final_state.get("error"):
            campaign.status = CampaignStatus.FAILED
            await _log_and_broadcast(
                session,
                campaign_id,
                "System",
                f"Workflow failed: {final_state.get('error')}",
                "ERROR",
            )
        else:
            campaign.status = CampaignStatus.COMPLETED
            original_count = (
                len(final_state.get("generated_copies", []))
                + len(final_state.get("generated_images", []))
                + len(final_state.get("generated_videos", []))
            )
            optimized_count = len(final_state.get("optimized_assets", []))
            await _log_and_broadcast(
                session,
                campaign_id,
                "System",
                f"Workflow completed. Generated {original_count} original + {optimized_count} optimized assets.",
            )

        session.add(campaign)
        session.commit()
