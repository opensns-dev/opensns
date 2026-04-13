"""Tests for TTS, BGM, and Audio Mixing pipeline."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.agents.state import AdCopy, GeneratedAudioAsset, GeneratedAsset
from app.services.audio.interfaces import TTSResult, MusicResult, AudioMixResult


class TestTTSGenerationNode:
    """Tests for tts_generation_node."""

    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self):
        """When tts_enabled=False, returns empty list immediately."""
        from app.services.agents.nodes import tts_generation_node

        state = {"tts_enabled": False}
        result = await tts_generation_node(state)
        assert result["generated_tts"] == []
        assert result["tts_done"] is True

    @pytest.mark.asyncio
    async def test_no_copies_returns_empty(self):
        """When no copies available, returns empty list."""
        from app.services.agents.nodes import tts_generation_node

        state = {"tts_enabled": True, "generated_copies": []}
        result = await tts_generation_node(state)
        assert result["generated_tts"] == []
        assert result["tts_done"] is True

    @pytest.mark.asyncio
    async def test_audio_data_saved_to_temp_file(self):
        """When TTS returns audio_data bytes, they are saved to a temp file."""
        from app.services.agents.nodes import tts_generation_node

        mock_tts = AsyncMock()
        mock_tts.generate_speech.return_value = TTSResult(
            audio_data=b"fake audio content",
            audio_url=None,
            duration=5.0,
            metadata={"engine": "test"},
        )

        state = {
            "tts_enabled": True,
            "generated_copies": [
                AdCopy(headline="Test", body="Body", cta="Buy", platform="instagram")
            ],
            "tts_voice_id": "nova",
            "default_tts_engine": "openai-tts",
        }

        with patch("app.services.agents.nodes._get_tts_engine", return_value=mock_tts):
            result = await tts_generation_node(state)

        assert len(result["generated_tts"]) == 1
        tts_asset = result["generated_tts"][0]
        assert tts_asset.asset_type == "tts"
        assert tts_asset.content != "tts_audio_data"
        assert os.path.exists(tts_asset.content)
        with open(tts_asset.content, "rb") as f:
            assert f.read() == b"fake audio content"
        os.unlink(tts_asset.content)

    @pytest.mark.asyncio
    async def test_audio_url_preferred_over_data(self):
        """When TTS returns audio_url, it's used directly (no temp file)."""
        from app.services.agents.nodes import tts_generation_node

        mock_tts = AsyncMock()
        mock_tts.generate_speech.return_value = TTSResult(
            audio_data=b"audio bytes",
            audio_url="https://example.com/speech.mp3",
            duration=3.0,
            metadata={},
        )

        state = {
            "tts_enabled": True,
            "generated_copies": [
                AdCopy(headline="H", body="B", cta="C", platform="facebook")
            ],
            "tts_voice_id": None,
            "default_tts_engine": "openai-tts",
        }

        with patch("app.services.agents.nodes._get_tts_engine", return_value=mock_tts):
            result = await tts_generation_node(state)

        assert len(result["generated_tts"]) == 1
        assert result["generated_tts"][0].content == "https://example.com/speech.mp3"

    @pytest.mark.asyncio
    async def test_engine_failure_returns_empty(self):
        """When TTS engine raises, returns empty list gracefully."""
        from app.services.agents.nodes import tts_generation_node

        mock_tts = AsyncMock()
        mock_tts.generate_speech.side_effect = RuntimeError("TTS failed")

        state = {
            "tts_enabled": True,
            "generated_copies": [
                AdCopy(headline="H", body="B", cta="C", platform="facebook")
            ],
            "tts_voice_id": None,
            "default_tts_engine": "openai-tts",
        }

        with patch("app.services.agents.nodes._get_tts_engine", return_value=mock_tts):
            result = await tts_generation_node(state)

        assert result["generated_tts"] == []
        assert result["tts_done"] is True

    @pytest.mark.asyncio
    async def test_no_engine_returns_empty(self):
        """When no TTS engine available, returns empty."""
        from app.services.agents.nodes import tts_generation_node

        state = {
            "tts_enabled": True,
            "generated_copies": [
                AdCopy(headline="H", body="B", cta="C", platform="facebook")
            ],
        }

        with patch("app.services.agents.nodes._get_tts_engine", return_value=None):
            result = await tts_generation_node(state)

        assert result["generated_tts"] == []
        assert result["tts_done"] is True


class TestBGMGenerationNode:
    """Tests for bgm_generation_node."""

    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self):
        """When bgm_enabled=False, returns empty list."""
        from app.services.agents.nodes import bgm_generation_node

        state = {"bgm_enabled": False}
        result = await bgm_generation_node(state)
        assert result["generated_bgm"] == []
        assert result["bgm_done"] is True

    @pytest.mark.asyncio
    async def test_audio_data_saved_to_temp_file(self):
        """When BGM returns audio_data bytes, they are saved to a temp file."""
        from app.services.agents.nodes import bgm_generation_node

        mock_bgm = AsyncMock()
        mock_bgm.generate_music.return_value = MusicResult(
            audio_data=b"bgm audio data here",
            audio_url=None,
            duration=15.0,
            metadata={"style": "corporate"},
        )

        state = {
            "bgm_enabled": True,
            "bgm_style": "corporate",
            "default_bgm_engine": "static-bgm",
        }

        with patch("app.services.agents.nodes._get_bgm_engine", return_value=mock_bgm):
            result = await bgm_generation_node(state)

        assert len(result["generated_bgm"]) == 1
        bgm_asset = result["generated_bgm"][0]
        assert bgm_asset.asset_type == "bgm"
        assert bgm_asset.content != "bgm_audio_data"
        assert os.path.exists(bgm_asset.content)
        with open(bgm_asset.content, "rb") as f:
            assert f.read() == b"bgm audio data here"
        os.unlink(bgm_asset.content)

    @pytest.mark.asyncio
    async def test_no_engine_returns_empty(self):
        """When no BGM engine available, returns empty."""
        from app.services.agents.nodes import bgm_generation_node

        state = {"bgm_enabled": True}
        with patch("app.services.agents.nodes._get_bgm_engine", return_value=None):
            result = await bgm_generation_node(state)
        assert result["generated_bgm"] == []
        assert result["bgm_done"] is True


class TestDownloadFile:
    """Tests for mixer._download_file."""

    @pytest.mark.asyncio
    async def test_local_file_copy(self, tmp_path):
        """Local file paths are copied instead of downloaded."""
        from app.services.audio.mixer import _download_file

        src = tmp_path / "source.mp3"
        src.write_bytes(b"local audio file")
        dest = tmp_path / "dest.mp3"

        result = await _download_file(str(src), dest)
        assert result is True
        assert dest.read_bytes() == b"local audio file"

    @pytest.mark.asyncio
    async def test_local_file_missing(self, tmp_path):
        """Missing local file returns False."""
        from app.services.audio.mixer import _download_file

        dest = tmp_path / "dest.mp3"
        result = await _download_file("/nonexistent/file.mp3", dest)
        assert result is False

    @pytest.mark.asyncio
    async def test_http_url_downloads(self, tmp_path):
        """HTTP URLs are downloaded via httpx."""
        from app.services.audio.mixer import _download_file

        mock_response = MagicMock()
        mock_response.content = b"downloaded audio"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        dest = tmp_path / "dest.mp3"
        with patch(
            "app.services.audio.mixer.httpx.AsyncClient", return_value=mock_client
        ):
            result = await _download_file("https://example.com/audio.mp3", dest)

        assert result is True
        assert dest.read_bytes() == b"downloaded audio"


class TestAudioMixingNode:
    """Tests for audio_mixing_node."""

    @pytest.mark.asyncio
    async def test_no_tts_no_bgm_returns_empty(self):
        """When no TTS/BGM assets, returns empty immediately."""
        from app.services.agents.nodes import audio_mixing_node

        state = {"generated_tts": [], "generated_bgm": []}
        result = await audio_mixing_node(state)
        assert result["mixed_videos"] == []
        assert result["audio_mixed"] is True

    @pytest.mark.asyncio
    async def test_placeholder_content_skipped(self):
        """TTS/BGM with placeholder content strings are skipped."""
        from app.services.agents.nodes import audio_mixing_node

        state = {
            "generated_tts": [
                GeneratedAudioAsset(
                    asset_type="tts", content="tts_audio_data", metadata={}
                )
            ],
            "generated_bgm": [
                GeneratedAudioAsset(
                    asset_type="bgm", content="bgm_audio_data", metadata={}
                )
            ],
            "generated_videos": [],
            "generated_ugc_videos": [],
        }
        result = await audio_mixing_node(state)
        assert result["mixed_videos"] == []
        assert result["audio_mixed"] is True

    @pytest.mark.asyncio
    async def test_local_path_accepted_for_video(self):
        """Videos with local file paths (not just HTTP) are processed."""
        from app.services.agents.nodes import audio_mixing_node
        from app.services.agents.state import GeneratedAsset

        state = {
            "generated_tts": [
                GeneratedAudioAsset(
                    asset_type="tts", content="/tmp/tts.mp3", metadata={}
                )
            ],
            "generated_bgm": [],
            "generated_videos": [
                GeneratedAsset(
                    asset_type="video",
                    content="/tmp/video.mp4",
                    platform="instagram",
                    metadata={},
                )
            ],
            "generated_ugc_videos": [],
        }

        mock_result = {"success": True, "video_url": "/tmp/mixed.mp4", "metadata": {}}

        with patch(
            "app.services.agents.nodes._dispatch_mix_task",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await audio_mixing_node(state)

        assert len(result["mixed_videos"]) == 1
        assert result["mixed_videos"][0].content == "/tmp/mixed.mp4"


class TestDispatchMixTask:
    """Tests for _dispatch_mix_task."""

    @pytest.mark.asyncio
    async def test_taskiq_failure_falls_back_to_direct_ffmpeg(self):
        """When TaskIQ/Redis unavailable, falls back to direct ffmpeg."""
        from app.services.agents.nodes import _dispatch_mix_task

        mock_mix_result = AudioMixResult(
            video_data=b"mixed video data",
            metadata={"engine": "ffmpeg"},
        )

        with (
            patch.dict("sys.modules", {"app.worker": None}),
            patch(
                "app.services.audio.mixer.ffmpeg_mix_audio",
                new_callable=AsyncMock,
                return_value=mock_mix_result,
            ),
        ):
            result = await _dispatch_mix_task(
                video_url="/tmp/test_video.mp4",
                narration_url="/tmp/narration.mp3",
                bgm_url=None,
            )

        assert result is not None
        assert result["success"] is True
        if os.path.exists(result["video_url"]):
            os.unlink(result["video_url"])

    @pytest.mark.asyncio
    async def test_both_taskiq_and_ffmpeg_fail_returns_none(self):
        """When both TaskIQ and direct ffmpeg fail, returns None."""
        from app.services.agents.nodes import _dispatch_mix_task

        with (
            patch.dict("sys.modules", {"app.worker": None}),
            patch(
                "app.services.audio.mixer.ffmpeg_mix_audio",
                new_callable=AsyncMock,
                side_effect=RuntimeError("ffmpeg not found"),
            ),
        ):
            result = await _dispatch_mix_task(
                video_url="/tmp/video.mp4",
                narration_url="/tmp/narr.mp3",
                bgm_url=None,
            )

        assert result is None


class TestAudioMixingNodeEdgeCases:
    """Additional edge case tests identified in code review."""

    @pytest.mark.asyncio
    async def test_ugc_video_mixed_with_bgm_only(self):
        """UGC videos get BGM mixed but no narration (already have voice)."""
        from app.services.agents.nodes import audio_mixing_node
        from app.services.agents.state import GeneratedAsset

        state = {
            "generated_tts": [],
            "generated_bgm": [
                GeneratedAudioAsset(
                    asset_type="bgm", content="/tmp/bgm.mp3", metadata={}
                )
            ],
            "generated_videos": [],
            "generated_ugc_videos": [
                GeneratedAsset(
                    asset_type="video",
                    content="http://127.0.0.1:8188/view?filename=ugc.mp4",
                    platform="instagram",
                    metadata={},
                )
            ],
        }

        mock_result = {
            "success": True,
            "video_url": "/tmp/ugc_mixed.mp4",
            "metadata": {},
        }

        with patch(
            "app.services.agents.nodes._dispatch_mix_task",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_dispatch:
            result = await audio_mixing_node(state)

        assert len(result["mixed_ugc_videos"]) == 1
        assert result["mixed_ugc_videos"][0].content == "/tmp/ugc_mixed.mp4"
        # UGC: narration_url should be None, preserve_original_audio=True
        mock_dispatch.assert_called_once_with(
            "http://127.0.0.1:8188/view?filename=ugc.mp4",
            None,
            "/tmp/bgm.mp3",
            preserve_original_audio=True,
            campaign_id=0,
        )

    @pytest.mark.asyncio
    async def test_fallback_videos_skipped(self):
        """Videos with metadata.fallback=True are not mixed."""
        from app.services.agents.nodes import audio_mixing_node
        from app.services.agents.state import GeneratedAsset

        state = {
            "generated_tts": [
                GeneratedAudioAsset(
                    asset_type="tts", content="/tmp/tts.mp3", metadata={}
                )
            ],
            "generated_bgm": [],
            "generated_videos": [
                GeneratedAsset(
                    asset_type="video",
                    content="http://example.com/fallback.mp4",
                    platform="facebook",
                    metadata={"fallback": True},
                ),
                GeneratedAsset(
                    asset_type="video",
                    content="http://example.com/real.mp4",
                    platform="instagram",
                    metadata={"fallback": False},
                ),
            ],
            "generated_ugc_videos": [],
        }

        mock_result = {
            "success": True,
            "video_url": "/tmp/mixed.mp4",
            "metadata": {},
        }

        with patch(
            "app.services.agents.nodes._dispatch_mix_task",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_dispatch:
            result = await audio_mixing_node(state)

        # Only non-fallback video should be mixed
        assert len(result["mixed_videos"]) == 1
        mock_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_audio_url_uses_audio_data(self):
        """When TTS returns empty string audio_url, audio_data is used instead."""
        from app.services.agents.nodes import tts_generation_node

        mock_tts = AsyncMock()
        mock_tts.generate_speech.return_value = TTSResult(
            audio_data=b"audio bytes here",
            audio_url="",  # empty string, falsy
            duration=3.0,
            metadata={"engine": "test"},
        )

        state = {
            "tts_enabled": True,
            "generated_copies": [
                AdCopy(headline="H", body="B", cta="C", platform="facebook")
            ],
            "tts_voice_id": None,
            "default_tts_engine": "openai-tts",
        }

        with patch("app.services.agents.nodes._get_tts_engine", return_value=mock_tts):
            result = await tts_generation_node(state)

        assert len(result["generated_tts"]) == 1
        content = result["generated_tts"][0].content
        # Should be a temp file path, not empty string
        assert content != ""
        assert os.path.exists(content)
        with open(content, "rb") as f:
            assert f.read() == b"audio bytes here"
        os.unlink(content)

    @pytest.mark.asyncio
    async def test_multiple_videos_all_mixed(self):
        """Multiple non-fallback videos are all processed."""
        from app.services.agents.nodes import audio_mixing_node
        from app.services.agents.state import GeneratedAsset

        state = {
            "generated_tts": [
                GeneratedAudioAsset(
                    asset_type="tts", content="/tmp/tts.mp3", metadata={}
                )
            ],
            "generated_bgm": [
                GeneratedAudioAsset(
                    asset_type="bgm", content="/tmp/bgm.mp3", metadata={}
                )
            ],
            "generated_videos": [
                GeneratedAsset(
                    asset_type="video",
                    content="http://example.com/v1.mp4",
                    platform="instagram",
                    metadata={},
                ),
                GeneratedAsset(
                    asset_type="video",
                    content="http://example.com/v2.mp4",
                    platform="facebook",
                    metadata={},
                ),
                GeneratedAsset(
                    asset_type="video",
                    content="http://example.com/v3.mp4",
                    platform="google_ads",
                    metadata={},
                ),
            ],
            "generated_ugc_videos": [],
        }

        call_count = 0

        async def mock_dispatch(video_url, narr, bgm, **kwargs):
            nonlocal call_count
            call_count += 1
            return {
                "success": True,
                "video_url": f"/tmp/mixed_{call_count}.mp4",
                "metadata": {},
            }

        with patch(
            "app.services.agents.nodes._dispatch_mix_task",
            side_effect=mock_dispatch,
        ):
            result = await audio_mixing_node(state)

        assert len(result["mixed_videos"]) == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_dispatch_failure_skips_video_gracefully(self):
        """When _dispatch_mix_task returns None, video is skipped (not added)."""
        from app.services.agents.nodes import audio_mixing_node
        from app.services.agents.state import GeneratedAsset

        state = {
            "generated_tts": [
                GeneratedAudioAsset(
                    asset_type="tts", content="/tmp/tts.mp3", metadata={}
                )
            ],
            "generated_bgm": [],
            "generated_videos": [
                GeneratedAsset(
                    asset_type="video",
                    content="http://example.com/v1.mp4",
                    platform="instagram",
                    metadata={},
                ),
            ],
            "generated_ugc_videos": [],
        }

        with patch(
            "app.services.agents.nodes._dispatch_mix_task",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await audio_mixing_node(state)

        assert result["mixed_videos"] == []
        assert result["audio_mixed"] is True


class TestCleanupTempFiles:
    """Tests for temp file cleanup mechanism."""

    def test_cleanup_removes_tracked_files(self, tmp_path):
        """cleanup_temp_files removes all tracked temp files."""
        from app.services.agents.nodes import (
            _save_to_temp,
            _temp_files,
            cleanup_temp_files,
        )

        # Clear any leftover state
        _temp_files.clear()

        # Create temp files via helper
        path1 = _save_to_temp(b"data1", ".mp3", "test_")
        path2 = _save_to_temp(b"data2", ".mp4", "test_")

        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert len(_temp_files.get(0, [])) == 2

        cleanup_temp_files()

        assert not os.path.exists(path1)
        assert not os.path.exists(path2)
        assert 0 not in _temp_files

    def test_cleanup_handles_already_deleted(self):
        """cleanup_temp_files doesn't crash if file already deleted."""
        from app.services.agents.nodes import _temp_files, cleanup_temp_files

        _temp_files.clear()
        _temp_files.setdefault(0, []).append("/tmp/nonexistent_file_12345.mp3")

        cleanup_temp_files()
        assert 0 not in _temp_files


class TestDownloadFilePathTraversal:
    @pytest.mark.asyncio
    async def test_non_temp_path_rejected(self):
        from app.services.audio.mixer import _download_file

        src = Path("/etc/hosts")
        dest = Path(tempfile.mkdtemp()) / "dest.txt"

        result = await _download_file(str(src), dest)
        assert result is False
        assert not dest.exists()

        dest.parent.rmdir()

    @pytest.mark.asyncio
    async def test_prefix_collision_rejected(self, tmp_path):
        """Path like /tmpXYZ/file passes startswith('/tmp') but is not a child."""
        from app.services.audio.mixer import _download_file

        src_dir = tmp_path / "abc"
        src_dir.mkdir()
        src_file = src_dir / "file.mp3"
        src_file.write_bytes(b"data")

        fake_tmpdir = str(tmp_path / "ab")

        dest = tmp_path / "dest.mp3"
        with patch(
            "app.services.audio.mixer.tempfile.gettempdir", return_value=fake_tmpdir
        ):
            result = await _download_file(str(src_file), dest)

        assert result is False
        assert not dest.exists()


class TestPipelineCleanupTiming:
    """Verify cleanup happens AFTER _save_final_state, not before."""

    def _make_mock_session(self, campaign_id):
        mock_campaign = MagicMock()
        mock_campaign.product_url = "https://example.com"
        mock_campaign.user_id = 1
        mock_campaign.brand_kit_id = None
        mock_campaign.status = "researching"

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_campaign
        mock_session_instance.__enter__ = MagicMock(return_value=mock_session_instance)
        mock_session_instance.__exit__ = MagicMock(return_value=False)
        return mock_session_instance

    @pytest.mark.asyncio
    async def test_cleanup_called_after_save(self):
        call_order = []

        async def mock_save(campaign_id, state):
            call_order.append("save")

        def mock_cleanup(campaign_id=0):
            call_order.append("cleanup")

        fake_state = {"current_step": "complete", "campaign_id": 99}

        async def mock_workflow(**kwargs):
            return fake_state

        mock_session = self._make_mock_session(99)

        with (
            patch(
                "app.services.pipeline.run_marketing_workflow",
                side_effect=mock_workflow,
            ),
            patch("app.services.pipeline._save_final_state", side_effect=mock_save),
            patch("app.services.pipeline.cleanup_temp_files", side_effect=mock_cleanup),
            patch("app.services.pipeline._get_user_api_config", return_value={}),
            patch("app.services.pipeline._log_and_broadcast", new_callable=AsyncMock),
            patch("app.services.pipeline._make_step_callback", return_value=None),
            patch("app.services.pipeline.Session", return_value=mock_session),
            patch("app.services.pipeline.engine"),
            patch("app.services.pipeline.is_storage_configured", return_value=True),
        ):
            from app.services.pipeline import run_campaign_pipeline

            await run_campaign_pipeline(campaign_id=99)

        assert call_order == ["save", "cleanup"]

    @pytest.mark.asyncio
    async def test_cleanup_called_on_workflow_error(self):
        call_order = []

        def mock_cleanup(campaign_id=0):
            call_order.append("cleanup")

        async def mock_workflow(**kwargs):
            raise RuntimeError("workflow exploded")

        mock_session = self._make_mock_session(99)

        with (
            patch(
                "app.services.pipeline.run_marketing_workflow",
                side_effect=mock_workflow,
            ),
            patch("app.services.pipeline.cleanup_temp_files", side_effect=mock_cleanup),
            patch("app.services.pipeline._get_user_api_config", return_value={}),
            patch("app.services.pipeline._log_and_broadcast", new_callable=AsyncMock),
            patch("app.services.pipeline._make_step_callback", return_value=None),
            patch("app.services.pipeline.Session", return_value=mock_session),
            patch("app.services.pipeline.engine"),
            patch("app.services.pipeline.is_storage_configured", return_value=True),
        ):
            from app.services.pipeline import run_campaign_pipeline

            with pytest.raises(RuntimeError, match="workflow exploded"):
                await run_campaign_pipeline(campaign_id=99)

        assert "cleanup" in call_order
