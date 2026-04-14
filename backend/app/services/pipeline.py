import json
import logging
import os

logger = logging.getLogger(__name__)

from app.models.models import (
    Campaign,
    CampaignStatus,
    AgentLog,
    Asset,
    AssetType,
    UserSettings,
    User,
    BrandKit,
)
from app.db import engine
from sqlmodel import Session, select
from app.services.agents.graph import run_marketing_workflow, resume_after_approval
from app.services.agents.nodes import cleanup_temp_files
from app.services.agents.state import AgentState
from app.api.websocket import send_agent_log
from app.core.credential_resolver import resolve_credential
from app.services.storage import is_storage_configured, upload_asset, generate_key


def _get_user_api_config(session: Session, user_id: int) -> dict:
    """Fetch and decrypt user's API configuration.

    Uses the new ProviderCredential table first, falling back to legacy UserSettings.
    """
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == user_id)
    ).first()

    if not user_settings:
        return {
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "heygen_api_key": None,
            "did_api_key": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "elevenlabs_api_key": None,
            "default_tts_engine": None,
            "default_bgm_engine": None,
            "tts_voice_id": None,
            "bgm_style": None,
            "tts_enabled": False,
            "bgm_enabled": False,
        }

    # Use credential resolver for new table + fallback to legacy
    openai_key, _ = resolve_credential(session, user_id, "openai")
    fal_key, _ = resolve_credential(session, user_id, "fal")
    firecrawl_key, _ = resolve_credential(session, user_id, "firecrawl")
    _, ollama_url = resolve_credential(session, user_id, "ollama")
    _, comfyui_url = resolve_credential(session, user_id, "comfyui")
    heygen_key, _ = resolve_credential(session, user_id, "heygen")
    did_key, _ = resolve_credential(session, user_id, "did")
    elevenlabs_key, _ = resolve_credential(session, user_id, "elevenlabs")

    # Log warnings for decryption failures
    if user_settings.openai_api_key and not openai_key:
        logger.warning("Failed to decrypt OpenAI API key for user %s", user_id)
    if user_settings.fal_api_key and not fal_key:
        logger.warning("Failed to decrypt Fal API key for user %s", user_id)
    if user_settings.firecrawl_api_key and not firecrawl_key:
        logger.warning("Failed to decrypt Firecrawl API key for user %s", user_id)

    return {
        "openai_api_key": openai_key,
        "fal_api_key": fal_key,
        "firecrawl_api_key": firecrawl_key,
        "ollama_url": ollama_url or user_settings.ollama_url,
        "comfyui_url": comfyui_url or user_settings.comfyui_url,
        "heygen_api_key": heygen_key,
        "did_api_key": did_key,
        "default_llm_engine": user_settings.default_llm_engine,
        "default_image_engine": user_settings.default_image_engine,
        "default_video_engine": user_settings.default_video_engine,
        "default_ugc_engine": user_settings.default_ugc_engine,
        "ugc_enabled": user_settings.ugc_enabled,
        "ugc_avatar_id": user_settings.ugc_avatar_id,
        "ugc_voice_id": user_settings.ugc_voice_id,
        "elevenlabs_api_key": elevenlabs_key,
        "default_tts_engine": user_settings.default_tts_engine,
        "default_bgm_engine": user_settings.default_bgm_engine,
        "tts_voice_id": user_settings.tts_voice_id,
        "bgm_style": user_settings.bgm_style,
        "tts_enabled": user_settings.tts_enabled,
        "bgm_enabled": user_settings.bgm_enabled,
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


_STEP_TO_STATUS = {
    "copy_generation": CampaignStatus.GENERATING,
    "image_generation": CampaignStatus.GENERATING,
    "video_generation": CampaignStatus.GENERATING,
}


def _make_step_callback(campaign_id: int):
    last_status = [None]

    async def on_step_change(step: str):
        target_status = _STEP_TO_STATUS.get(step)
        if target_status and target_status != last_status[0]:
            last_status[0] = target_status
            with Session(engine) as session:
                campaign = session.get(Campaign, campaign_id)
                if campaign and campaign.status != target_status:
                    campaign.status = target_status
                    session.add(campaign)
                    session.commit()
                    await _log_and_broadcast(
                        session,
                        campaign_id,
                        "System",
                        f"Pipeline entered {step} phase",
                    )

    return on_step_change


async def run_campaign_pipeline(campaign_id: int, requires_approval: bool = False):
    if not is_storage_configured():
        raise RuntimeError(
            "Object storage is not configured. Set STORAGE_ENDPOINT_URL, "
            "STORAGE_ACCESS_KEY_ID, STORAGE_SECRET_ACCESS_KEY, and "
            "STORAGE_PUBLIC_URL environment variables."
        )
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            return

        product_url = campaign.product_url
        user_id = campaign.user_id

        user_config = _get_user_api_config(session, user_id)

        brand_kit_data = None
        if campaign.brand_kit_id:
            brand_kit = session.get(BrandKit, campaign.brand_kit_id)
            if brand_kit and brand_kit.user_id == user_id:
                try:
                    values = (
                        json.loads(brand_kit.brand_values)
                        if brand_kit.brand_values
                        else []
                    )
                except (json.JSONDecodeError, TypeError):
                    values = []
                brand_kit_data = {
                    "name": brand_kit.name,
                    "logo_url": brand_kit.logo_url,
                    "primary_color": brand_kit.primary_color,
                    "secondary_color": brand_kit.secondary_color,
                    "accent_color": brand_kit.accent_color,
                    "font_heading": brand_kit.font_heading,
                    "font_body": brand_kit.font_body,
                    "tone_of_voice": brand_kit.tone_of_voice,
                    "brand_values": values,
                    "target_audience": brand_kit.target_audience,
                    "guidelines": brand_kit.guidelines,
                }

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
            brand_kit=brand_kit_data,
            on_step_change=_make_step_callback(campaign_id),
        )
    except Exception as e:
        cleanup_temp_files(campaign_id)
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
        # Don't cleanup — temp files may be needed after approval resume
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
    cleanup_temp_files(campaign_id)
    return final_state


async def approve_and_resume(campaign_id: int):
    if not is_storage_configured():
        raise RuntimeError(
            "Object storage is not configured. Set STORAGE_ENDPOINT_URL, "
            "STORAGE_ACCESS_KEY_ID, STORAGE_SECRET_ACCESS_KEY, and "
            "STORAGE_PUBLIC_URL environment variables."
        )
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
        cleanup_temp_files(campaign_id)
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
    cleanup_temp_files(campaign_id)
    return final_state


async def _upload_asset_to_storage(
    content: str,
    campaign_id: int,
    asset_type: str,
    index: int,
    ext: str,
    content_type: str,
) -> str:
    if not content or not (
        content.startswith("http://")
        or content.startswith("https://")
        or os.path.exists(content)
    ):
        raise ValueError(
            f"Invalid content for upload: {content[:80] if content else 'None'}"
        )
    key = generate_key(campaign_id, asset_type, index, ext)
    return await upload_asset(content, key, content_type)


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
        for image_idx, image in enumerate(generated_images):
            image.content = await _upload_asset_to_storage(
                image.content,
                campaign_id,
                "image",
                image_idx,
                "png",
                "image/png",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.IMAGE,
                content=image.content,
                asset_metadata=json.dumps(image.metadata),
            )
            session.add(asset)

        generated_videos = final_state.get("generated_videos", [])
        for video_idx, video in enumerate(generated_videos):
            video.content = await _upload_asset_to_storage(
                video.content,
                campaign_id,
                "video",
                video_idx,
                "mp4",
                "video/mp4",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.VIDEO,
                content=video.content,
                asset_metadata=json.dumps(video.metadata),
            )
            session.add(asset)

        # BUG FIX: Persist generated UGC videos
        generated_ugc_videos = final_state.get("generated_ugc_videos", [])
        for ugc_idx, ugc_video in enumerate(generated_ugc_videos):
            ugc_video.content = await _upload_asset_to_storage(
                ugc_video.content,
                campaign_id,
                "ugc_video",
                ugc_idx,
                "mp4",
                "video/mp4",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.VIDEO,
                content=ugc_video.content,
                asset_metadata=json.dumps({**ugc_video.metadata, "type": "ugc"}),
            )
            session.add(asset)

        # Persist mixed videos (audio mixed)
        mixed_videos = final_state.get("mixed_videos", [])
        for mixed_idx, mixed_video in enumerate(mixed_videos):
            mixed_video.content = await _upload_asset_to_storage(
                mixed_video.content,
                campaign_id,
                "mixed_video",
                mixed_idx,
                "mp4",
                "video/mp4",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.VIDEO,
                content=mixed_video.content,
                asset_metadata=json.dumps(
                    {**mixed_video.metadata, "audio_mixed": True}
                ),
            )
            session.add(asset)

        # Persist mixed UGC videos (audio mixed)
        mixed_ugc_videos = final_state.get("mixed_ugc_videos", [])
        for mixed_ugc_idx, mixed_ugc in enumerate(mixed_ugc_videos):
            mixed_ugc.content = await _upload_asset_to_storage(
                mixed_ugc.content,
                campaign_id,
                "mixed_ugc_video",
                mixed_ugc_idx,
                "mp4",
                "video/mp4",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.VIDEO,
                content=mixed_ugc.content,
                asset_metadata=json.dumps(
                    {**mixed_ugc.metadata, "type": "ugc", "audio_mixed": True}
                ),
            )
            session.add(asset)

        # Persist generated TTS as AUDIO assets
        generated_tts = final_state.get("generated_tts", [])
        for tts_idx, tts in enumerate(generated_tts):
            tts.content = await _upload_asset_to_storage(
                tts.content,
                campaign_id,
                "tts",
                tts_idx,
                "mp3",
                "audio/mpeg",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.AUDIO,
                content=tts.content,
                asset_metadata=json.dumps({**tts.metadata, "audio_type": "tts"}),
            )
            session.add(asset)

        # Persist generated BGM as AUDIO assets
        generated_bgm = final_state.get("generated_bgm", [])
        for bgm_idx, bgm in enumerate(generated_bgm):
            bgm.content = await _upload_asset_to_storage(
                bgm.content,
                campaign_id,
                "bgm",
                bgm_idx,
                "mp3",
                "audio/mpeg",
            )
            asset = Asset(
                campaign_id=campaign_id,
                type=AssetType.AUDIO,
                content=bgm.content,
                asset_metadata=json.dumps({**bgm.metadata, "audio_type": "bgm"}),
            )
            session.add(asset)

        if user:
            from app.services.usage import (
                use_image_credits,
                use_video_credits,
                use_tts_credits,
            )

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
            # BUG FIX: Charge credits for UGC videos
            real_ugc_videos = [
                vid
                for vid in generated_ugc_videos
                if not vid.metadata.get("fallback", False) and vid.content
            ]
            # Charge credits for TTS
            real_tts = [
                tts
                for tts in generated_tts
                if tts.content and tts.content != "tts_audio_data"
            ]
            if real_images:
                use_image_credits(session, user, len(real_images), campaign_id)
            if real_videos:
                use_video_credits(session, user, len(real_videos), campaign_id)
            if real_ugc_videos:
                use_video_credits(session, user, len(real_ugc_videos), campaign_id)
            if real_tts:
                use_tts_credits(session, user, len(real_tts), campaign_id)

        for opt_idx, optimized in enumerate(final_state.get("optimized_assets", [])):
            asset_type = (
                AssetType.IMAGE if optimized.asset_type == "image" else AssetType.VIDEO
            )
            opt_ext = "png" if optimized.asset_type == "image" else "mp4"
            opt_ct = "image/png" if optimized.asset_type == "image" else "video/mp4"
            optimized.content = await _upload_asset_to_storage(
                optimized.content,
                campaign_id,
                "optimized",
                opt_idx,
                opt_ext,
                opt_ct,
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
            copy_count = len(final_state.get("generated_copies", []))
            image_count = len(final_state.get("generated_images", []))
            video_count = len(final_state.get("generated_videos", []))
            ugc_count = len(final_state.get("generated_ugc_videos", []))
            mixed_count = len(final_state.get("mixed_videos", []))
            mixed_ugc_count = len(final_state.get("mixed_ugc_videos", []))
            tts_count = len(final_state.get("generated_tts", []))
            bgm_count = len(final_state.get("generated_bgm", []))
            optimized_count = len(final_state.get("optimized_assets", []))

            original_count = copy_count + image_count + video_count + ugc_count
            audio_count = tts_count + bgm_count

            await _log_and_broadcast(
                session,
                campaign_id,
                "System",
                f"Workflow completed. Generated {original_count} original ({copy_count} copies, {image_count} images, {video_count} videos, {ugc_count} UGC) + {optimized_count} optimized + {mixed_count + mixed_ugc_count} audio-mixed + {audio_count} audio assets.",
            )

        session.add(campaign)
        session.commit()
