"""Tests for ComfyUI image and video adapters with portability foundation."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.image.comfyui_adapter import ComfyUIAdapter
from app.services.video.comfyui_video_adapter import ComfyUIVideoAdapter
from app.services.video.interfaces import VideoGenerationRequest
from app.core.interfaces import AdCreative
from app.services.comfyui_portability import (
    MissingNodeError,
    MissingModelError,
    ComfyUICompatibilityError,
    NodeAliasResolver,
    ComfyUIDiscovery,
)


class TestComfyUIAdapter:
    """Tests for ComfyUI image adapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked discovery."""
        adapter = ComfyUIAdapter(base_url="http://localhost:8188")
        # Mock discovery methods
        adapter.discovery.fetch_object_info = AsyncMock(
            return_value={
                "LoadImageBase64": {},
                "SAMModelLoader": {},
                "GroundingDinoSAMSegment": {},
                "CheckpointLoaderSimple": {},
                "CLIPTextEncode": {},
                "InpaintModelConditioning": {},
                "KSampler": {},
                "VAEDecode": {},
                "ImageCompositeMasked": {},
                "SaveImage": {},
            }
        )
        # Pre-populate the alias resolver cache
        adapter.alias_resolver._available_cache = {
            "LoadImageBase64",
            "SAMModelLoader",
            "GroundingDinoSAMSegment",
            "CheckpointLoaderSimple",
            "CLIPTextEncode",
            "InpaintModelConditioning",
            "KSampler",
            "VAEDecode",
            "ImageCompositeMasked",
            "SaveImage",
        }
        return adapter

    @pytest.mark.asyncio
    async def test_generate_ad_image_success(self, adapter):
        """Test successful image generation."""
        mock_history = {
            "test-prompt-id": {
                "status": {"status_str": "success"},
                "outputs": {
                    "11": {
                        "images": [
                            {
                                "filename": "opensns_ad_0001.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
            }
        }
        mock_image_data = b"fake_image_data"

        with (
            patch("httpx.AsyncClient.post") as mock_post,
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"prompt_id": "test-prompt-id"},
                raise_for_status=lambda: None,
            )
            mock_get.side_effect = [
                MagicMock(
                    status_code=200,
                    json=lambda: mock_history,
                    raise_for_status=lambda: None,
                ),
                MagicMock(
                    status_code=200,
                    content=mock_image_data,
                    raise_for_status=lambda: None,
                ),
            ]

            creative = AdCreative(
                title="Test Ad",
                body="Test body",
                platform="instagram",
                image_prompt="professional product photo",
            )
            result = await adapter.generate_ad_image(b"fake_image", creative)

        assert result.image_data == mock_image_data
        assert result.metadata["filename"] == "opensns_ad_0001.png"
        assert result.metadata["workflow"] == "background_replacement"

    @pytest.mark.asyncio
    async def test_node_alias_resolution(self, adapter):
        """Test that node aliases are properly resolved."""
        # Use alternative node names
        adapter.alias_resolver._available_cache = {
            "Load Image (Base64)",  # Aliased name
            "SAM Model Loader",  # Aliased name
            "GroundingDinoSAMSegment",
            "Load Checkpoint",  # Aliased name
            "CLIP Text Encode",  # Aliased name
            "InpaintModelConditioning",
            "KSampler",
            "VAE Decode",  # Aliased name
            "ImageCompositeMasked",
            "Save Image",  # Aliased name
        }

        mock_history = {
            "test-prompt-id": {
                "status": {"status_str": "success"},
                "outputs": {
                    "11": {
                        "images": [
                            {
                                "filename": "test.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
            }
        }

        with (
            patch("httpx.AsyncClient.post") as mock_post,
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"prompt_id": "test-prompt-id"},
                raise_for_status=lambda: None,
            )
            mock_get.side_effect = [
                MagicMock(
                    status_code=200,
                    json=lambda: mock_history,
                    raise_for_status=lambda: None,
                ),
                MagicMock(
                    status_code=200,
                    content=b"image",
                    raise_for_status=lambda: None,
                ),
            ]

            creative = AdCreative(
                title="Test Ad",
                body="Test body",
                platform="instagram",
            )
            result = await adapter.generate_ad_image(b"fake_image", creative)

        assert result.image_data == b"image"


class TestComfyUIVideoAdapter:
    """Tests for ComfyUI video adapter."""

    @pytest.fixture
    def adapter(self):
        adapter = ComfyUIVideoAdapter(base_url="http://localhost:8188")
        adapter.discovery.fetch_object_info = AsyncMock(
            return_value={
                "LoadImage": {},
                "CheckpointLoaderSimple": {},
                "CLIPTextEncode": {},
                "ImageScale": {},
                "VAEEncode": {},
                "VAEDecode": {},
                "RepeatLatentBatch": {},
                "KSampler": {},
                "ADE_LoadAnimateDiffModel": {},
                "ADE_ApplyAnimateDiffModel": {},
                "ADE_UseEvolvedSampling": {},
                "VHS_VideoCombine": {},
            }
        )
        adapter.alias_resolver._available_cache = {
            "LoadImage",
            "CheckpointLoaderSimple",
            "CLIPTextEncode",
            "ImageScale",
            "VAEEncode",
            "VAEDecode",
            "RepeatLatentBatch",
            "KSampler",
            "ADE_LoadAnimateDiffModel",
            "ADE_ApplyAnimateDiffModel",
            "ADE_UseEvolvedSampling",
            "VHS_VideoCombine",
        }
        return adapter

    @pytest.mark.asyncio
    async def test_generate_video_success(self, adapter):
        mock_history = {
            "test-prompt-id": {
                "status": {"status_str": "success"},
                "outputs": {
                    "12": {
                        "gifs": [
                            {
                                "filename": "opensns_video_0001.mp4",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
            }
        }

        with (
            patch("httpx.AsyncClient.post") as mock_post,
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"prompt_id": "test-prompt-id"},
                raise_for_status=lambda: None,
            )
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_history,
                raise_for_status=lambda: None,
            )

            request = VideoGenerationRequest(
                images=["/path/to/image.png"],
                duration=5.0,
                aspect_ratio="9:16",
            )
            result = await adapter.generate_video(request)

        assert "opensns_video_0001.mp4" in result.video_url
        assert result.duration == 5.0
        assert result.metadata["output_key"] == "gifs"

    @pytest.mark.asyncio
    async def test_animatediff_node_alias_resolution(self, adapter):
        adapter.alias_resolver._available_cache = {
            "LoadImage",
            "Load Checkpoint",
            "CLIP Text Encode",
            "Image Scale",
            "VAE Encode",
            "VAE Decode",
            "Repeat Latent Batch",
            "KSampler",
            "Load AnimateDiff Model",
            "Apply AnimateDiff Model",
            "Use Evolved Sampling",
            "Video Combine",
        }

        mock_history = {
            "test-prompt-id": {
                "status": {"status_str": "success"},
                "outputs": {
                    "12": {
                        "gifs": [
                            {"filename": "video.mp4", "subfolder": "", "type": "output"}
                        ]
                    }
                },
            }
        }

        with (
            patch("httpx.AsyncClient.post") as mock_post,
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"prompt_id": "test-prompt-id"},
                raise_for_status=lambda: None,
            )
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_history,
                raise_for_status=lambda: None,
            )

            request = VideoGenerationRequest(
                images=["/path/to/image.png"],
                duration=3.0,
            )
            result = await adapter.generate_video(request)

        assert result.video_url is not None

    @pytest.mark.asyncio
    async def test_missing_animatediff_nodes_error(self, adapter):
        adapter.discovery.fetch_object_info = AsyncMock(
            return_value={"LoadImage": {}, "SaveImage": {}}
        )
        adapter.alias_resolver._available_cache = {"LoadImage", "SaveImage"}

        request = VideoGenerationRequest(
            images=["/path/to/image.png"],
            duration=5.0,
        )

        with pytest.raises(ComfyUICompatibilityError) as exc_info:
            await adapter.generate_video(request)

        error_msg = str(exc_info.value).lower()
        assert "missing" in error_msg or "not found" in error_msg

    @pytest.mark.asyncio
    async def test_unsupported_output_format(self, adapter):
        mock_history = {
            "test-prompt-id": {
                "status": {"status_str": "success"},
                "outputs": {"12": {"unknown_format": [{"filename": "test.xyz"}]}},
            }
        }

        with (
            patch("httpx.AsyncClient.post") as mock_post,
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"prompt_id": "test-prompt-id"},
                raise_for_status=lambda: None,
            )
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_history,
                raise_for_status=lambda: None,
            )

            request = VideoGenerationRequest(
                images=["/path/to/image.png"],
                duration=5.0,
            )

            with pytest.raises(ComfyUICompatibilityError) as exc_info:
                await adapter.generate_video(request)

            assert "no video output found" in str(exc_info.value).lower()


class TestComfyUIPortabilityFoundation:
    """Tests for the portability foundation components."""

    def test_node_alias_resolver(self):
        """Test node alias resolution."""
        resolver = NodeAliasResolver()

        # Set up available cache
        resolver._available_cache = {"LoadImage", "SaveImage", "Load Image (Base64)"}

        # Test direct match
        assert resolver.resolve("load_image", ["LoadImage", "SaveImage"]) == "LoadImage"

        # Test alias match
        assert (
            resolver.resolve("load_image_base64", ["Load Image (Base64)", "SaveImage"])
            == "Load Image (Base64)"
        )

    def test_missing_node_error(self):
        """Test MissingNodeError creation."""
        error = MissingNodeError("TestNode", ["Alias1", "Alias2"])
        assert "TestNode" in str(error)
        assert "Alias1" in str(error)

    def test_missing_model_error(self):
        """Test MissingModelError creation."""
        error = MissingModelError("sdxl_base", "checkpoints")
        assert "sdxl_base" in str(error)
        assert "checkpoints" in str(error)
