"""
Tests for UGC video adapters (HeyGen, D-ID, SadTalker).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.video.interfaces import (
    AvatarInfo,
    UGCVideoRequest,
    VideoGenerationResult,
    VoiceInfo,
)
from app.services.video.heygen_adapter import HeyGenAdapter
from app.services.video.did_adapter import DIDAdapter
from app.services.video.sadtalker_adapter import SadTalkerAdapter


class TestHeyGenAdapter:
    """Tests for HeyGenAdapter"""

    def test_supports_ugc(self):
        """Test that HeyGen supports UGC."""
        adapter = HeyGenAdapter(api_key="test-key")
        assert adapter.supports_ugc() is True

    @pytest.mark.asyncio
    async def test_list_avatars_success(self):
        """Test listing avatars from HeyGen API."""
        adapter = HeyGenAdapter(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "avatars": [
                    {
                        "avatar_id": "avatar-1",
                        "avatar_name": "Test Avatar",
                        "preview_image_url": "https://example.com/preview.jpg",
                        "gender": "female",
                        "avatar_style": "normal",
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            avatars = await adapter.list_avatars()

        assert len(avatars) == 1
        assert avatars[0].avatar_id == "avatar-1"
        assert avatars[0].name == "Test Avatar"
        assert isinstance(avatars[0], AvatarInfo)

    @pytest.mark.asyncio
    async def test_list_avatars_no_api_key(self):
        """Test listing avatars without API key returns empty."""
        adapter = HeyGenAdapter(api_key=None)
        adapter.api_key = None
        avatars = await adapter.list_avatars()
        assert avatars == []

    @pytest.mark.asyncio
    async def test_list_voices_success(self):
        """Test listing voices from HeyGen API."""
        adapter = HeyGenAdapter(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "voices": [
                    {
                        "voice_id": "voice-1",
                        "display_name": "Jenny",
                        "language": "en-US",
                        "gender": "female",
                        "preview_audio": "https://example.com/audio.mp3",
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            voices = await adapter.list_voices()

        assert len(voices) == 1
        assert voices[0].voice_id == "voice-1"
        assert voices[0].language == "en-US"
        assert isinstance(voices[0], VoiceInfo)

    @pytest.mark.asyncio
    async def test_generate_ugc_video_success(self):
        """Test generating UGC video through HeyGen."""
        adapter = HeyGenAdapter(api_key="test-key")
        adapter.poll_interval = 0.01
        adapter.max_poll_attempts = 2

        request = UGCVideoRequest(
            script="Hello, this is a test video.",
            avatar_id="avatar-1",
            voice_id="voice-1",
            aspect_ratio="9:16",
        )

        create_response = MagicMock()
        create_response.json.return_value = {"data": {"video_id": "vid-123"}}
        create_response.raise_for_status = MagicMock()

        status_response = MagicMock()
        status_response.json.return_value = {
            "data": {
                "status": "completed",
                "video_url": "https://example.com/video.mp4",
                "duration": 10.5,
            }
        }
        status_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=create_response)
            mock_instance.get = AsyncMock(return_value=status_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await adapter.generate_ugc_video(request)

        assert isinstance(result, VideoGenerationResult)
        assert result.video_url == "https://example.com/video.mp4"
        assert result.duration == 10.5
        assert result.metadata["engine"] == "heygen"


class TestDIDAdapter:
    """Tests for DIDAdapter"""

    def test_supports_ugc(self):
        """Test that D-ID supports UGC."""
        adapter = DIDAdapter(api_key="test-key")
        assert adapter.supports_ugc() is True

    @pytest.mark.asyncio
    async def test_list_avatars_success(self):
        """Test listing avatars (presenters) from D-ID API."""
        adapter = DIDAdapter(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "presenters": [
                {
                    "presenter_id": "presenter-1",
                    "name": "Amy",
                    "thumbnail_url": "https://example.com/thumb.jpg",
                    "gender": "female",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            avatars = await adapter.list_avatars()

        assert len(avatars) == 1
        assert avatars[0].avatar_id == "presenter-1"
        assert avatars[0].name == "Amy"

    @pytest.mark.asyncio
    async def test_list_voices_returns_microsoft_voices(self):
        """Test that D-ID returns Microsoft TTS voices."""
        adapter = DIDAdapter(api_key="test-key")
        voices = await adapter.list_voices()

        assert len(voices) > 0
        assert all(isinstance(v, VoiceInfo) for v in voices)
        assert any("en-US" in v.language for v in voices)

    @pytest.mark.asyncio
    async def test_generate_ugc_video_success(self):
        """Test generating UGC video through D-ID."""
        adapter = DIDAdapter(api_key="test-key")
        adapter.poll_interval = 0.01
        adapter.max_poll_attempts = 2

        request = UGCVideoRequest(
            script="Hello from D-ID test.",
            avatar_id="presenter-1",
            voice_id="en-US-JennyNeural",
        )

        create_response = MagicMock()
        create_response.json.return_value = {"id": "talk-123"}
        create_response.raise_for_status = MagicMock()

        status_response = MagicMock()
        status_response.json.return_value = {
            "status": "done",
            "result_url": "https://example.com/did-video.mp4",
            "duration": 8.0,
        }
        status_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=create_response)
            mock_instance.get = AsyncMock(return_value=status_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await adapter.generate_ugc_video(request)

        assert isinstance(result, VideoGenerationResult)
        assert result.video_url == "https://example.com/did-video.mp4"
        assert result.metadata["engine"] == "d-id"


class TestSadTalkerAdapter:
    """Tests for SadTalkerAdapter"""

    def test_supports_ugc(self):
        """Test that SadTalker supports UGC."""
        adapter = SadTalkerAdapter(endpoint_url="http://localhost:7860")
        assert adapter.supports_ugc() is True

    @pytest.mark.asyncio
    async def test_list_avatars_returns_avatars_from_api(self):
        """Test that SadTalker returns avatars from API."""
        adapter = SadTalkerAdapter(endpoint_url="http://localhost:7860")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "avatars": [
                {"id": "avatar1", "name": "Avatar 1", "gender": "female"},
                {"id": "avatar2", "name": "Avatar 2", "gender": "male"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            avatars = await adapter.list_avatars()

        assert len(avatars) == 2
        assert avatars[0].avatar_id == "avatar1"
        assert avatars[1].avatar_id == "avatar2"

    @pytest.mark.asyncio
    async def test_list_avatars_fallback_on_error(self):
        """Test that SadTalker returns default avatars on API error."""
        adapter = SadTalkerAdapter(endpoint_url="http://localhost:7860")

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            avatars = await adapter.list_avatars()

        assert len(avatars) == 2
        assert avatars[0].name == "Default Female"
        assert avatars[1].name == "Default Male"

    @pytest.mark.asyncio
    async def test_list_voices_returns_tts_options(self):
        """Test that SadTalker returns TTS voice options."""
        adapter = SadTalkerAdapter(endpoint_url="http://localhost:7860")
        voices = await adapter.list_voices()

        assert len(voices) > 0
        assert all(isinstance(v, VoiceInfo) for v in voices)

    @pytest.mark.asyncio
    async def test_generate_ugc_video_success(self):
        """Test generating UGC video through SadTalker."""
        adapter = SadTalkerAdapter(endpoint_url="http://localhost:7860")
        adapter.poll_interval = 0.01
        adapter.max_poll_attempts = 2

        request = UGCVideoRequest(
            script="Hello from SadTalker.",
            avatar_id="avatar1.jpg",
            voice_id="edge-tts-en",
        )

        generate_response = MagicMock()
        generate_response.json.return_value = {"task_id": "task-456"}
        generate_response.raise_for_status = MagicMock()

        status_response = MagicMock()
        status_response.json.return_value = {
            "status": "completed",
            "video_url": "http://localhost:7860/outputs/video.mp4",
            "duration": 5.0,
        }
        status_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=generate_response)
            mock_instance.get = AsyncMock(return_value=status_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await adapter.generate_ugc_video(request)

        assert isinstance(result, VideoGenerationResult)
        assert result.metadata["engine"] == "sadtalker"


class TestUGCVideoRequest:
    """Tests for UGCVideoRequest model."""

    def test_create_request_minimal(self):
        """Test creating request with minimal fields."""
        request = UGCVideoRequest(script="Test script")
        assert request.script == "Test script"
        assert request.language == "en"
        assert request.aspect_ratio == "9:16"

    def test_create_request_full(self):
        """Test creating request with all fields."""
        request = UGCVideoRequest(
            script="Full test script",
            avatar_id="avatar-123",
            voice_id="voice-456",
            language="ko",
            aspect_ratio="16:9",
            background_color="#ffffff",
            background_image_url="https://example.com/bg.jpg",
        )
        assert request.avatar_id == "avatar-123"
        assert request.language == "ko"
        assert request.background_color == "#ffffff"
