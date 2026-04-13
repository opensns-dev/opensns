"""
Tests for repurpose pipeline service.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlmodel import Session

from app.models.models import (
    RepurposeJob,
    RepurposeStatus,
    RepurposeContent,
    ContentPlatform,
    ToneStyle,
    User,
    UserSettings,
)
from app.services.repurpose.pipeline import (
    _get_openai_api_key,
    _get_llm_engine_name,
    run_repurpose_pipeline,
)


class TestGetOpenaiApiKey:
    """Tests for _get_openai_api_key function."""

    def test_no_settings_returns_app_default(self, session: Session):
        """Test returns app_settings.OPENAI_API_KEY when user has no settings."""
        from app.core.config import settings as app_settings

        result = _get_openai_api_key(session, 999)

        assert result == app_settings.OPENAI_API_KEY

    def test_with_settings_returns_decrypted_key(
        self, session: Session, test_user: User
    ):
        """Test returns decrypted key when user has settings with encrypted key."""
        from app.core.encryption import encrypt_api_key
        from app.core.config import settings as app_settings

        # Create user settings with encrypted key
        settings = session.get(UserSettings, test_user.id)
        if not settings:
            settings = UserSettings(user_id=test_user.id)
            session.add(settings)

        settings.openai_api_key = encrypt_api_key(
            "sk-user-openai-key", app_settings.API_KEY_ENCRYPTION_KEY
        )
        session.commit()

        result = _get_openai_api_key(session, test_user.id)

        assert result == "sk-user-openai-key"

    def test_decryption_failure_returns_app_default(
        self, session: Session, test_user: User
    ):
        """Test returns app_settings.OPENAI_API_KEY when decryption fails."""
        from app.core.config import settings as app_settings

        # Create user settings with invalid encrypted key
        settings = session.get(UserSettings, test_user.id)
        if not settings:
            settings = UserSettings(user_id=test_user.id)
            session.add(settings)

        settings.openai_api_key = "invalid-encrypted-key"
        session.commit()

        result = _get_openai_api_key(session, test_user.id)

        assert result == app_settings.OPENAI_API_KEY


class TestGetLlmEngineName:
    """Tests for _get_llm_engine_name function."""

    def test_no_settings_returns_default(self, session: Session):
        """Test returns app_settings.DEFAULT_LLM_ENGINE when user has no settings."""
        from app.core.config import settings as app_settings

        result = _get_llm_engine_name(session, 999)

        assert result == app_settings.DEFAULT_LLM_ENGINE

    def test_with_settings_returns_user_preference(
        self, session: Session, test_user: User
    ):
        """Test returns user's engine preference when set."""
        # Create user settings with custom engine
        settings = session.get(UserSettings, test_user.id)
        if not settings:
            settings = UserSettings(user_id=test_user.id)
            session.add(settings)

        settings.default_llm_engine = "ollama"
        session.commit()

        result = _get_llm_engine_name(session, test_user.id)

        assert result == "ollama"


class TestRunRepurposePipeline:
    """Tests for run_repurpose_pipeline function."""

    @pytest.mark.asyncio
    @patch("app.services.repurpose.pipeline.Session")
    @patch("app.services.repurpose.pipeline.engine_registry")
    @patch("app.services.repurpose.pipeline.extract_audio")
    @patch("app.services.repurpose.pipeline.transcribe_audio")
    @patch("app.services.repurpose.pipeline.ContentGenerator")
    @patch("app.services.repurpose.pipeline._broadcast_progress")
    @patch("app.services.repurpose.pipeline.use_credits")
    @patch(
        "app.services.repurpose.pipeline._get_openai_api_key",
        return_value="sk-test-key",
    )
    @patch(
        "app.services.repurpose.pipeline._get_llm_engine_name", return_value="openai"
    )
    async def test_success_flow(
        self,
        mock_get_llm_name,
        mock_get_api_key,
        mock_use_credits,
        mock_broadcast,
        mock_generator_class,
        mock_transcribe,
        mock_extract,
        mock_registry,
        mock_session_class,
        session: Session,
        test_user: User,
    ):
        """Test successful repurpose pipeline execution."""
        # Create repurpose job
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://youtube.com/watch?v=test123",
            tone_style=ToneStyle.FRIENDLY,
            target_platforms=json.dumps(
                [ContentPlatform.NAVER_BLOG, ContentPlatform.X_THREAD]
            ),
            status=RepurposeStatus.PENDING,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # Mock the Session context manager to return our test session
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock extract_audio
        mock_extract.return_value = (
            "/tmp/test/audio.mp3",
            {"title": "Test Video", "duration": 120},
        )

        # Mock transcribe_audio
        mock_transcribe.return_value = ("This is a test transcript", [])

        # Mock LLM engine
        mock_llm = MagicMock()
        mock_registry.get_llm_engine.return_value = mock_llm

        # Mock ContentGenerator
        mock_generator = MagicMock()
        mock_generator.generate_summary_and_key_points = AsyncMock(
            return_value=("Summary of video", ["Point 1", "Point 2"])
        )
        mock_generator.generate_all = AsyncMock(
            return_value=[
                {"platform": "NAVER_BLOG", "content": "Blog content", "metadata": {}},
                {"platform": "X_THREAD", "content": "Thread content", "metadata": {}},
            ]
        )
        mock_generator_class.return_value = mock_generator

        # Run pipeline
        await run_repurpose_pipeline(job.id)

        # Verify job status progression
        session.refresh(job)
        assert job.status == RepurposeStatus.COMPLETED
        assert job.video_title == "Test Video"
        assert job.video_duration == 120
        assert job.transcript == "This is a test transcript"
        assert job.summary == "Summary of video"

        # Verify content was created
        contents = (
            session.query(RepurposeContent)
            .filter(RepurposeContent.job_id == job.id)
            .all()
        )
        assert len(contents) == 2

        # Check content platforms
        platforms = [c.platform for c in contents]
        assert ContentPlatform.NAVER_BLOG in platforms
        assert ContentPlatform.X_THREAD in platforms

        # Verify credits were used
        mock_use_credits.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.repurpose.pipeline.Session")
    async def test_nonexistent_job_returns_early(
        self, mock_session_class, session: Session
    ):
        """Test returns early when job doesn't exist."""
        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Run pipeline with non-existent job ID
        result = await run_repurpose_pipeline(99999)

        # Should return None (early return)
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.repurpose.pipeline.Session")
    @patch("app.services.repurpose.pipeline.engine_registry")
    @patch("app.services.repurpose.pipeline.extract_audio")
    @patch("app.services.repurpose.pipeline.transcribe_audio")
    @patch("app.services.repurpose.pipeline.ContentGenerator")
    @patch("app.services.repurpose.pipeline._broadcast_progress")
    @patch("app.services.repurpose.pipeline.use_credits")
    @patch(
        "app.services.repurpose.pipeline._get_openai_api_key",
        return_value="sk-test-key",
    )
    @patch(
        "app.services.repurpose.pipeline._get_llm_engine_name", return_value="openai"
    )
    async def test_pipeline_with_segments(
        self,
        mock_get_llm_name,
        mock_get_api_key,
        mock_use_credits,
        mock_broadcast,
        mock_generator_class,
        mock_transcribe,
        mock_extract,
        mock_registry,
        mock_session_class,
        session: Session,
        test_user: User,
    ):
        """Test pipeline with transcript segments."""
        # Create repurpose job
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://youtube.com/watch?v=segments456",
            tone_style=ToneStyle.FORMAL,
            target_platforms=json.dumps(
                [ContentPlatform.INSTAGRAM, ContentPlatform.SHORT_CLIP]
            ),
            status=RepurposeStatus.PENDING,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock extract_audio
        mock_extract.return_value = (
            "/tmp/test/audio2.mp3",
            {"title": "Segmented Video", "duration": 300},
        )

        # Mock transcribe_audio with segments
        segments = [
            {"start": 0, "end": 10, "text": "First part"},
            {"start": 10, "end": 20, "text": "Second part"},
        ]
        mock_transcribe.return_value = ("First part Second part", segments)

        # Mock LLM engine
        mock_llm = MagicMock()
        mock_registry.get_llm_engine.return_value = mock_llm

        # Mock ContentGenerator
        mock_generator = MagicMock()
        mock_generator.generate_summary_and_key_points = AsyncMock(
            return_value=("Video summary", ["Key point 1", "Key point 2"])
        )
        mock_generator.generate_all = AsyncMock(
            return_value=[
                {
                    "platform": "INSTAGRAM",
                    "content": "Instagram post content",
                    "metadata": {"hashtags": ["#test"]},
                },
                {
                    "platform": "SHORT_CLIP",
                    "content": "Short clip script",
                    "metadata": {"duration": 60},
                },
            ]
        )
        mock_generator_class.return_value = mock_generator

        # Run pipeline
        await run_repurpose_pipeline(job.id)

        # Verify job has transcript segments stored
        session.refresh(job)
        assert job.transcript_segments is not None
        stored_segments = json.loads(job.transcript_segments)
        assert len(stored_segments) == 2
        assert stored_segments[0]["text"] == "First part"

        # Verify content metadata was stored
        contents = (
            session.query(RepurposeContent)
            .filter(RepurposeContent.job_id == job.id)
            .all()
        )
        assert len(contents) == 2

        # Check metadata
        for content in contents:
            metadata = json.loads(content.content_metadata)
            assert "hashtags" in metadata or "duration" in metadata

    @pytest.mark.asyncio
    @patch("app.services.repurpose.pipeline.Session")
    @patch("app.services.repurpose.pipeline.engine_registry")
    @patch("app.services.repurpose.pipeline.extract_audio")
    @patch("app.services.repurpose.pipeline._broadcast_progress")
    async def test_no_api_key_raises_error(
        self,
        mock_broadcast,
        mock_extract,
        mock_registry,
        mock_session_class,
        session: Session,
        test_user: User,
    ):
        """Test pipeline raises error when no API key is available."""
        from app.core.config import settings as app_settings

        # Create repurpose job
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://youtube.com/watch?v=noapi789",
            tone_style=ToneStyle.CASUAL,
            target_platforms=json.dumps([ContentPlatform.NAVER_BLOG]),
            status=RepurposeStatus.PENDING,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock extract_audio
        mock_extract.return_value = (
            "/tmp/test/audio3.mp3",
            {"title": "No API Video", "duration": 60},
        )

        # Temporarily clear the app settings API key
        original_key = app_settings.OPENAI_API_KEY
        app_settings.OPENAI_API_KEY = None

        try:
            # Run pipeline - should handle the error
            await run_repurpose_pipeline(job.id)

            # Verify job status is FAILED
            session.refresh(job)
            assert job.status == RepurposeStatus.FAILED
            assert "API" in job.error or "api" in job.error.lower()
        finally:
            # Restore the API key
            app_settings.OPENAI_API_KEY = original_key

    @pytest.mark.asyncio
    @patch("app.services.repurpose.pipeline.Session")
    @patch("app.services.repurpose.pipeline.engine_registry")
    @patch("app.services.repurpose.pipeline.extract_audio")
    @patch("app.services.repurpose.pipeline.transcribe_audio")
    @patch("app.services.repurpose.pipeline.ContentGenerator")
    @patch("app.services.repurpose.pipeline._broadcast_progress")
    @patch("app.services.repurpose.pipeline.use_credits")
    @patch(
        "app.services.repurpose.pipeline._get_openai_api_key",
        return_value="sk-test-key",
    )
    @patch(
        "app.services.repurpose.pipeline._get_llm_engine_name", return_value="openai"
    )
    async def test_all_platforms_generated(
        self,
        mock_get_llm_name,
        mock_get_api_key,
        mock_use_credits,
        mock_broadcast,
        mock_generator_class,
        mock_transcribe,
        mock_extract,
        mock_registry,
        mock_session_class,
        session: Session,
        test_user: User,
    ):
        """Test that content is generated for all target platforms."""
        # Create repurpose job with all platforms
        all_platforms = [
            ContentPlatform.NAVER_BLOG,
            ContentPlatform.X_THREAD,
            ContentPlatform.INSTAGRAM,
            ContentPlatform.BRUNCH,
            ContentPlatform.NAVER_POST,
            ContentPlatform.SHORT_CLIP,
        ]
        job = RepurposeJob(
            user_id=test_user.id,
            youtube_url="https://youtube.com/watch?v=allplatforms",
            tone_style=ToneStyle.FRIENDLY,
            target_platforms=json.dumps(all_platforms),
            status=RepurposeStatus.PENDING,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # Mock the Session context manager
        mock_session_class.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        # Mock extract_audio
        mock_extract.return_value = (
            "/tmp/test/audio4.mp3",
            {"title": "All Platforms Video", "duration": 600},
        )

        # Mock transcribe_audio
        mock_transcribe.return_value = ("Full transcript text", [])

        # Mock LLM engine
        mock_llm = MagicMock()
        mock_registry.get_llm_engine.return_value = mock_llm

        # Mock ContentGenerator to return content for all platforms
        mock_results = [
            {
                "platform": platform.value,
                "content": f"Content for {platform.value}",
                "metadata": {},
            }
            for platform in all_platforms
        ]
        mock_generator = MagicMock()
        mock_generator.generate_summary_and_key_points = AsyncMock(
            return_value=("Summary", ["Point 1", "Point 2", "Point 3"])
        )
        mock_generator.generate_all = AsyncMock(return_value=mock_results)
        mock_generator_class.return_value = mock_generator

        # Run pipeline
        await run_repurpose_pipeline(job.id)

        # Verify all platforms have content
        contents = (
            session.query(RepurposeContent)
            .filter(RepurposeContent.job_id == job.id)
            .all()
        )
        assert len(contents) == len(all_platforms)

        # Verify each platform is represented
        content_platforms = [c.platform for c in contents]
        for platform in all_platforms:
            assert platform in content_platforms
