"""
Tests for campaign pipeline service.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlmodel import Session

from app.models.models import (
    Campaign,
    CampaignStatus,
    User,
    UserSettings,
    Asset,
    AssetType,
)
from app.services.pipeline import (
    _get_user_api_config,
    run_campaign_pipeline,
    approve_and_resume,
    _save_final_state,
)
from app.services.agents.state import AgentState, AdCopy, GeneratedAsset


class TestGetUserApiConfig:
    """Tests for _get_user_api_config function."""

    def test_no_settings(self, session: Session):
        """Test returns all None values when user has no settings."""
        result = _get_user_api_config(session, 999)

        assert result["openai_api_key"] is None
        assert result["fal_api_key"] is None
        assert result["firecrawl_api_key"] is None
        assert result["ollama_url"] is None
        assert result["comfyui_url"] is None
        assert result["default_llm_engine"] is None
        assert result["default_image_engine"] is None
        assert result["default_video_engine"] is None

    def test_with_settings_and_encrypted_keys(self, session: Session, test_user: User):
        """Test returns decrypted keys when user has settings with encrypted keys."""
        from app.core.encryption import encrypt_api_key
        from app.core.config import settings as app_settings

        # Create user settings with encrypted keys
        settings = session.get(UserSettings, test_user.id)
        if not settings:
            settings = UserSettings(user_id=test_user.id)
            session.add(settings)

        # Encrypt API keys
        settings.openai_api_key = encrypt_api_key(
            "sk-test-openai-key", app_settings.API_KEY_ENCRYPTION_KEY
        )
        settings.fal_api_key = encrypt_api_key(
            "fal-test-key", app_settings.API_KEY_ENCRYPTION_KEY
        )
        settings.firecrawl_api_key = encrypt_api_key(
            "fc-test-key", app_settings.API_KEY_ENCRYPTION_KEY
        )
        settings.ollama_url = "http://localhost:11434"
        settings.comfyui_url = "http://localhost:8188"
        settings.default_llm_engine = "ollama"
        settings.default_image_engine = "comfyui"
        settings.default_video_engine = "comfyui-video"
        session.commit()

        result = _get_user_api_config(session, test_user.id)

        assert result["openai_api_key"] == "sk-test-openai-key"
        assert result["fal_api_key"] == "fal-test-key"
        assert result["firecrawl_api_key"] == "fc-test-key"
        assert result["ollama_url"] == "http://localhost:11434"
        assert result["comfyui_url"] == "http://localhost:8188"
        assert result["default_llm_engine"] == "ollama"
        assert result["default_image_engine"] == "comfyui"
        assert result["default_video_engine"] == "comfyui-video"

    def test_decryption_failure_returns_none(self, session: Session, test_user: User):
        """Test returns None for key when decryption fails."""
        # Create user settings with invalid encrypted key
        settings = session.get(UserSettings, test_user.id)
        if not settings:
            settings = UserSettings(user_id=test_user.id)
            session.add(settings)

        # Set an invalid encrypted key (not valid format)
        settings.openai_api_key = "invalid-encrypted-key"
        settings.fal_api_key = "v2:invalid:salt:encrypted"  # Invalid v2 format
        session.commit()

        result = _get_user_api_config(session, test_user.id)

        # Should return None for keys that fail decryption
        assert result["openai_api_key"] is None
        assert result["fal_api_key"] is None


class TestRunCampaignPipeline:
    """Tests for run_campaign_pipeline function."""

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.run_marketing_workflow")
    @patch("app.services.pipeline._save_final_state")
    @patch("app.services.pipeline.send_agent_log")
    async def test_success_flow(
        self,
        mock_send_log,
        mock_save_state,
        mock_workflow,
        mock_session_class,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test successful pipeline execution."""
        # Create campaign
        campaign = Campaign(
            title="Test Campaign",
            product_url="https://example.com/product",
            user_id=test_user.id,
            status=CampaignStatus.PENDING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager to return our test session
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock workflow to return successful state
        final_state: AgentState = {
            "campaign_id": campaign.id,
            "user_id": test_user.id,
            "product_url": "https://example.com/product",
            "product_context": "",
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "research_data": None,
            "competitor_insights": [],
            "angles": [],
            "generated_copies": [],
            "generated_images": [],
            "generated_videos": [],
            "generated_ugc_videos": [],
            "optimized_assets": [],
            "performance_predictions": [],
            "verification_results": [],
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "completed",
            "retry_count": 0,
            "max_retries": 3,
            "error": None,
            "is_complete": True,
            "copy_done": True,
            "visual_done": True,
            "ugc_done": True,
            "requires_approval": False,
            "is_approved": False,
        }
        mock_workflow.return_value = final_state

        # Run pipeline
        result = await run_campaign_pipeline(campaign.id, requires_approval=False)

        # Verify workflow was called
        mock_workflow.assert_called_once()
        call_kwargs = mock_workflow.call_args.kwargs
        assert call_kwargs["campaign_id"] == campaign.id
        assert call_kwargs["user_id"] == test_user.id
        assert call_kwargs["product_url"] == "https://example.com/product"
        assert call_kwargs["requires_approval"] is False

        # Verify final state was saved
        mock_save_state.assert_called_once_with(campaign.id, final_state)

        # Verify campaign status was updated to RESEARCHING during execution
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.RESEARCHING

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.run_marketing_workflow")
    @patch("app.services.pipeline.send_agent_log")
    async def test_failure_flow(
        self,
        mock_send_log,
        mock_workflow,
        mock_session_class,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test pipeline failure handling."""
        # Create campaign
        campaign = Campaign(
            title="Failing Campaign",
            product_url="https://example.com/fail",
            user_id=test_user.id,
            status=CampaignStatus.PENDING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock workflow to raise exception
        mock_workflow.side_effect = Exception("Workflow failed")

        # Run pipeline - should raise
        with pytest.raises(Exception, match="Workflow failed"):
            await run_campaign_pipeline(campaign.id, requires_approval=False)

        # Verify campaign status was set to FAILED
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.FAILED

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.run_marketing_workflow")
    @patch("app.services.pipeline.send_agent_log")
    async def test_approval_flow(
        self,
        mock_send_log,
        mock_workflow,
        mock_session_class,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test pipeline with approval requirement."""
        # Create campaign
        campaign = Campaign(
            title="Approval Campaign",
            product_url="https://example.com/approval",
            user_id=test_user.id,
            status=CampaignStatus.PENDING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock workflow to return state awaiting approval
        final_state: AgentState = {
            "campaign_id": campaign.id,
            "user_id": test_user.id,
            "product_url": "https://example.com/approval",
            "product_context": "",
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "research_data": None,
            "competitor_insights": [],
            "angles": [],
            "generated_copies": [],
            "generated_images": [],
            "generated_videos": [],
            "generated_ugc_videos": [],
            "optimized_assets": [],
            "performance_predictions": [],
            "verification_results": [],
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "awaiting_approval",
            "retry_count": 0,
            "max_retries": 3,
            "error": None,
            "is_complete": False,
            "copy_done": False,
            "visual_done": False,
            "ugc_done": False,
            "requires_approval": True,
            "is_approved": False,
        }
        mock_workflow.return_value = final_state

        # Run pipeline with approval required
        result = await run_campaign_pipeline(campaign.id, requires_approval=True)

        # Verify campaign status was set to AWAITING_APPROVAL
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.AWAITING_APPROVAL

        # Verify result is the final state
        assert result["current_step"] == "awaiting_approval"


class TestApproveAndResume:
    """Tests for approve_and_resume function."""

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.resume_after_approval")
    @patch("app.services.pipeline._save_final_state")
    @patch("app.services.pipeline.send_agent_log")
    async def test_approve_and_resume_success(
        self,
        mock_send_log,
        mock_save_state,
        mock_resume,
        mock_session_class,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test successful approval and resume."""
        # Create campaign awaiting approval
        campaign = Campaign(
            title="Resume Campaign",
            product_url="https://example.com/resume",
            user_id=test_user.id,
            status=CampaignStatus.AWAITING_APPROVAL,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock resume to return successful state
        final_state: AgentState = {
            "campaign_id": campaign.id,
            "user_id": test_user.id,
            "product_url": "https://example.com/resume",
            "product_context": "",
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "research_data": None,
            "competitor_insights": [],
            "angles": [],
            "generated_copies": [],
            "generated_images": [],
            "generated_videos": [],
            "generated_ugc_videos": [],
            "optimized_assets": [],
            "performance_predictions": [],
            "verification_results": [],
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "completed",
            "retry_count": 0,
            "max_retries": 3,
            "error": None,
            "is_complete": True,
            "copy_done": True,
            "visual_done": True,
            "ugc_done": True,
            "requires_approval": True,
            "is_approved": True,
        }
        mock_resume.return_value = final_state

        # Run approve and resume
        result = await approve_and_resume(campaign.id)

        # Verify campaign status was set to RESEARCHING during resume
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.RESEARCHING

        # Verify resume was called
        mock_resume.assert_called_once_with(campaign.id)

        # Verify final state was saved
        mock_save_state.assert_called_once_with(campaign.id, final_state)

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.resume_after_approval")
    @patch("app.services.pipeline.send_agent_log")
    async def test_approve_and_resume_failure(
        self,
        mock_send_log,
        mock_resume,
        mock_session_class,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test approval and resume failure handling."""
        # Create campaign awaiting approval
        campaign = Campaign(
            title="Failing Resume Campaign",
            product_url="https://example.com/fail-resume",
            user_id=test_user.id,
            status=CampaignStatus.AWAITING_APPROVAL,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock resume to raise exception
        mock_resume.side_effect = Exception("Resume failed")

        # Run approve and resume - should raise
        with pytest.raises(Exception, match="Resume failed"):
            await approve_and_resume(campaign.id)

        # Verify campaign status was set to FAILED
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.FAILED


class TestSaveFinalState:
    """Tests for _save_final_state function."""

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch(
        "app.services.pipeline._upload_asset_to_storage",
        new_callable=AsyncMock,
        return_value="https://storage.example.com/uploaded.png",
    )
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.send_agent_log")
    @patch("app.services.usage.use_image_credits")
    @patch("app.services.usage.use_video_credits")
    async def test_save_copies_images_videos(
        self,
        mock_video_credits,
        mock_image_credits,
        mock_send_log,
        mock_session_class,
        mock_upload,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test saving copies, images, and videos as assets."""
        # Create campaign
        campaign = Campaign(
            title="Asset Campaign",
            product_url="https://example.com/assets",
            user_id=test_user.id,
            status=CampaignStatus.GENERATING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Create final state with assets
        final_state: AgentState = {
            "campaign_id": campaign.id,
            "user_id": test_user.id,
            "product_url": "https://example.com/assets",
            "product_context": "",
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "research_data": None,
            "competitor_insights": [],
            "angles": [],
            "generated_copies": [
                AdCopy(
                    headline="Test Headline",
                    body="Test body content",
                    cta="Click here",
                    platform="instagram",
                )
            ],
            "generated_images": [
                GeneratedAsset(
                    asset_type="image",
                    content="https://example.com/image1.png",
                    platform="instagram",
                    metadata={"fallback": False},
                ),
                GeneratedAsset(
                    asset_type="image",
                    content="https://example.com/image2.png",
                    platform="facebook",
                    metadata={"fallback": True},  # Fallback image
                ),
            ],
            "generated_videos": [
                GeneratedAsset(
                    asset_type="video",
                    content="https://example.com/video1.mp4",
                    platform="tiktok",
                    metadata={"fallback": False},
                )
            ],
            "generated_ugc_videos": [],
            "optimized_assets": [],
            "performance_predictions": [],
            "verification_results": [],
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "completed",
            "retry_count": 0,
            "max_retries": 3,
            "error": None,
            "is_complete": True,
            "copy_done": True,
            "visual_done": True,
            "ugc_done": True,
            "requires_approval": False,
            "is_approved": False,
        }

        # Run save final state
        await _save_final_state(campaign.id, final_state)

        # Verify campaign status is COMPLETED
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.COMPLETED

        # Query assets from database
        assets = session.query(Asset).filter(Asset.campaign_id == campaign.id).all()

        # Should have 4 assets: 1 copy + 2 images + 1 video
        assert len(assets) == 4

        # Check copy asset
        copy_assets = [a for a in assets if a.type == AssetType.COPY]
        assert len(copy_assets) == 1
        assert "Test Headline" in copy_assets[0].content
        assert "Test body content" in copy_assets[0].content
        assert "Click here" in copy_assets[0].content
        metadata = json.loads(copy_assets[0].asset_metadata)
        assert metadata["platform"] == "instagram"

        # Check image assets
        image_assets = [a for a in assets if a.type == AssetType.IMAGE]
        assert len(image_assets) == 2

        # Check video assets
        video_assets = [a for a in assets if a.type == AssetType.VIDEO]
        assert len(video_assets) == 1

        # Verify credits were charged for non-fallback assets only
        # 1 real image (not fallback) + 1 real video (not fallback)
        mock_image_credits.assert_called_once()
        mock_video_credits.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch(
        "app.services.pipeline._upload_asset_to_storage",
        new_callable=AsyncMock,
        return_value="https://storage.example.com/uploaded.png",
    )
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.send_agent_log")
    async def test_save_with_error(
        self,
        mock_send_log,
        mock_session_class,
        mock_upload,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test saving final state with error marks campaign as FAILED."""
        # Create campaign
        campaign = Campaign(
            title="Error Campaign",
            product_url="https://example.com/error",
            user_id=test_user.id,
            status=CampaignStatus.GENERATING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Create final state with error
        final_state: AgentState = {
            "campaign_id": campaign.id,
            "user_id": test_user.id,
            "product_url": "https://example.com/error",
            "product_context": "",
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "research_data": None,
            "competitor_insights": [],
            "angles": [],
            "generated_copies": [],
            "generated_images": [],
            "generated_videos": [],
            "generated_ugc_videos": [],
            "optimized_assets": [],
            "performance_predictions": [],
            "verification_results": [],
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "verification",
            "retry_count": 3,
            "max_retries": 3,
            "error": "Generation failed after max retries",
            "is_complete": False,
            "copy_done": False,
            "visual_done": False,
            "ugc_done": False,
            "requires_approval": False,
            "is_approved": False,
        }

        # Run save final state
        await _save_final_state(campaign.id, final_state)

        # Verify campaign status is FAILED
        session.refresh(campaign)
        assert campaign.status == CampaignStatus.FAILED

    @pytest.mark.asyncio
    @patch("app.services.pipeline.is_storage_configured", return_value=True)
    @patch(
        "app.services.pipeline._upload_asset_to_storage",
        new_callable=AsyncMock,
        return_value="https://storage.example.com/uploaded.png",
    )
    @patch("app.services.pipeline.Session")
    @patch("app.services.pipeline.send_agent_log")
    async def test_save_optimized_assets(
        self,
        mock_send_log,
        mock_session_class,
        mock_upload,
        mock_storage_configured,
        session: Session,
        test_user: User,
    ):
        """Test saving optimized assets."""
        # Create campaign
        campaign = Campaign(
            title="Optimized Campaign",
            product_url="https://example.com/optimized",
            user_id=test_user.id,
            status=CampaignStatus.GENERATING,
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Create final state with optimized assets
        final_state: AgentState = {
            "campaign_id": campaign.id,
            "user_id": test_user.id,
            "product_url": "https://example.com/optimized",
            "product_context": "",
            "openai_api_key": None,
            "fal_api_key": None,
            "firecrawl_api_key": None,
            "ollama_url": None,
            "comfyui_url": None,
            "default_llm_engine": None,
            "default_image_engine": None,
            "default_video_engine": None,
            "default_ugc_engine": None,
            "ugc_enabled": False,
            "ugc_avatar_id": None,
            "ugc_voice_id": None,
            "research_data": None,
            "competitor_insights": [],
            "angles": [],
            "generated_copies": [],
            "generated_images": [],
            "generated_videos": [],
            "generated_ugc_videos": [],
            "optimized_assets": [
                GeneratedAsset(
                    asset_type="image",
                    content="https://example.com/optimized-image.png",
                    platform="instagram",
                    metadata={"optimized": True},
                ),
                GeneratedAsset(
                    asset_type="video",
                    content="https://example.com/optimized-video.mp4",
                    platform="tiktok",
                    metadata={"optimized": True},
                ),
            ],
            "performance_predictions": [],
            "verification_results": [],
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "completed",
            "retry_count": 0,
            "max_retries": 3,
            "error": None,
            "is_complete": True,
            "copy_done": True,
            "visual_done": True,
            "ugc_done": True,
            "requires_approval": False,
            "is_approved": False,
        }

        # Run save final state
        await _save_final_state(campaign.id, final_state)

        # Query assets from database
        assets = session.query(Asset).filter(Asset.campaign_id == campaign.id).all()

        # Should have 2 optimized assets
        assert len(assets) == 2

        # Check optimized assets have correct metadata
        for asset in assets:
            metadata = json.loads(asset.asset_metadata)
            assert metadata["platform_optimized"] is True
            assert metadata["optimized"] is True
