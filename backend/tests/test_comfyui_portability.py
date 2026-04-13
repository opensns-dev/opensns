"""Tests for ComfyUI portability foundation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64

from app.services.comfyui_portability import (
    WorkflowManifest,
    NodeDefinition,
    NodeInput,
    NodeOutput,
    WorkflowOutput,
    InputType,
    ComfyUIDiscovery,
    NodeAliasResolver,
    ModelRegistry,
    WorkflowLoader,
    MissingNodeError,
    MissingModelError,
    ComfyUICompatibilityError,
)
from app.services.comfyui_portability.manifest import (
    BACKGROUND_REPLACEMENT_MANIFEST,
    ANIMATEDIFF_V3_MANIFEST,
)
from app.services.image.comfyui_adapter import ComfyUIAdapter
from app.services.video.comfyui_video_adapter import ComfyUIVideoAdapter
from app.services.video.interfaces import VideoGenerationRequest
from app.core.interfaces import AdCreative


class TestWorkflowManifest:
    """Test workflow manifest functionality."""

    def test_manifest_creation(self):
        """Test creating a basic workflow manifest."""
        manifest = WorkflowManifest(
            name="test_workflow",
            description="A test workflow",
            nodes={
                "1": NodeDefinition(
                    logical_type="load_image",
                    alias_priority=["LoadImage"],
                    inputs={"image": NodeInput(type=InputType.STRING)},
                    outputs=[NodeOutput(name="IMAGE", type="IMAGE", slot_index=0)],
                )
            },
            outputs=[
                WorkflowOutput(
                    node_id="1", output_key="images", output_type="image", slot_index=0
                )
            ],
        )
        assert manifest.name == "test_workflow"
        assert manifest.version == "1.0.0"

    def test_predefined_manifests_exist(self):
        """Test that predefined manifests are available."""
        assert BACKGROUND_REPLACEMENT_MANIFEST.name == "background_replacement"
        assert ANIMATEDIFF_V3_MANIFEST.name == "animatediff_v3"

    def test_to_comfyui_workflow_basic(self):
        """Test converting manifest to ComfyUI workflow."""
        resolver = NodeAliasResolver()
        registry = ModelRegistry()

        workflow = BACKGROUND_REPLACEMENT_MANIFEST.to_comfyui_workflow(
            node_resolver=resolver,
            model_registry=registry,
            parameters={
                "image_base64": "base64_encoded_image",
                "prompt": "test prompt",
            },
        )

        # Check workflow structure
        assert "1" in workflow
        assert "11" in workflow  # SaveImage node
        assert workflow["1"]["class_type"] == "LoadImageBase64"
        # The image input should be set from parameters
        assert workflow["1"]["inputs"]["image_base64"] == "base64_encoded_image"


class TestNodeAliasResolver:
    """Test node alias resolution."""

    def test_default_aliases(self):
        """Test default alias mappings."""
        resolver = NodeAliasResolver()

        # Test without discovery (returns first alias)
        assert resolver.resolve("load_image") == "LoadImage"
        assert resolver.resolve("checkpoint_loader") == "CheckpointLoaderSimple"

    def test_register_alias(self):
        """Test registering custom aliases."""
        resolver = NodeAliasResolver()
        resolver.register_alias("custom_node", ["CustomNodeV1", "CustomNodeV2"])

        assert resolver.resolve("custom_node") == "CustomNodeV1"

    def test_priority_override(self):
        """Test that priority list overrides default aliases."""
        resolver = NodeAliasResolver()
        result = resolver.resolve("load_image", priority=["CustomLoadImage"])

        assert result == "CustomLoadImage"

    @pytest.mark.asyncio
    async def test_resolve_with_discovery(self):
        """Test resolution with discovery."""
        discovery = MagicMock()
        discovery.get_available_nodes = AsyncMock(
            return_value=["LoadImage", "KSampler"]
        )

        resolver = NodeAliasResolver(discovery)
        result = await resolver.resolve_with_discovery("load_image")

        assert result == "LoadImage"


class TestModelRegistry:
    """Test model registry functionality."""

    def test_default_mappings(self):
        """Test default model mappings."""
        registry = ModelRegistry()

        # Test checkpoint resolution
        assert (
            registry.resolve("sdxl_base", "checkpoints") == "sd_xl_base_1.0.safetensors"
        )
        assert registry.resolve("sam_vit_h", "sams") == "sam_vit_h_4b8939.pth"

    def test_register_model(self):
        """Test registering custom model mappings."""
        registry = ModelRegistry()
        registry.register_model("custom_model", "checkpoints", "custom.safetensors")

        assert registry.resolve("custom_model", "checkpoints") == "custom.safetensors"

    def test_resolve_unknown_model(self):
        """Test resolving unknown model returns the logical id."""
        registry = ModelRegistry()

        # Unknown model returns the logical_id as-is
        assert registry.resolve("unknown_model", "checkpoints") == "unknown_model"

    def test_list_models(self):
        """Test listing available models."""
        registry = ModelRegistry()
        models = registry.list_models("checkpoints")

        assert "sdxl_base" in models
        assert "sdxl_refiner" in models


class TestComfyUIAdapter:
    """Test ComfyUI image adapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with portability components."""
        adapter = ComfyUIAdapter(base_url="http://localhost:8188")

        assert adapter.base_url == "http://localhost:8188"
        assert adapter.discovery is not None
        assert adapter.alias_resolver is not None
        assert adapter.model_registry is not None
        assert adapter.workflow_loader is not None

    def test_custom_model_mappings(self):
        """Test adapter accepts custom model mappings."""
        adapter = ComfyUIAdapter(
            base_url="http://localhost:8188",
            model_mappings={"sdxl_base": "custom_model.safetensors"},
        )

        assert (
            adapter.model_registry.resolve("sdxl_base", "checkpoints")
            == "custom_model.safetensors"
        )

    @pytest.mark.asyncio
    async def test_generate_ad_image_missing_node_error(self):
        """Test that missing node errors are properly raised."""
        adapter = ComfyUIAdapter()

        # Mock the discovery to return empty node list
        adapter.discovery.get_available_nodes = AsyncMock(return_value=[])
        adapter.alias_resolver._available_cache = set()

        creative = AdCreative(
            title="Test", body="Test body", platform="instagram", image_prompt="test"
        )

        # Should raise ComfyUICompatibilityError when nodes are missing
        with pytest.raises(ComfyUICompatibilityError):
            await adapter.generate_ad_image(b"fake_image_data", creative)


class TestComfyUIVideoAdapter:
    """Test ComfyUI video adapter."""

    def test_adapter_initialization(self):
        """Test video adapter initializes correctly."""
        adapter = ComfyUIVideoAdapter(base_url="http://localhost:8188")

        assert adapter.base_url == "http://localhost:8188"
        assert adapter.discovery is not None
        assert adapter.alias_resolver is not None

    @pytest.mark.asyncio
    async def test_video_generation_request_validation(self):
        """Test that video generation validates inputs."""
        adapter = ComfyUIVideoAdapter()

        request = VideoGenerationRequest(images=[], duration=5.0)

        with pytest.raises(ValueError, match="At least one image is required"):
            await adapter.generate_video(request)


class TestWorkflowLoader:
    """Test workflow loader functionality."""

    def test_loader_initialization(self):
        """Test loader initializes with presets."""
        loader = WorkflowLoader()

        presets = loader.list_presets()
        assert "background_replacement" in presets
        assert "animatediff_v3" in presets

    def test_get_preset(self):
        """Test getting predefined presets."""
        loader = WorkflowLoader()

        manifest = loader.get_preset("background_replacement")
        assert manifest is not None
        assert manifest.name == "background_replacement"

    def test_get_nonexistent_preset(self):
        """Test getting non-existent preset returns None."""
        loader = WorkflowLoader()

        manifest = loader.get_preset("nonexistent")
        assert manifest is None


class TestComfyUICompatibilityError:
    """Test compatibility error handling."""

    def test_missing_node_error(self):
        """Test MissingNodeError formatting."""
        error = MissingNodeError(
            logical_node="custom_node",
            attempted_aliases=["CustomNodeV1", "CustomNodeV2"],
            available_nodes=["OtherNode"],
        )

        assert "custom_node" in str(error)
        assert "CustomNodeV1" in str(error)
        assert error.logical_node == "custom_node"

    def test_missing_model_error(self):
        """Test MissingModelError formatting."""
        error = MissingModelError(
            logical_model="custom_model",
            model_type="checkpoints",
            available_models=["model1.safetensors"],
        )

        assert "custom_model" in str(error)
        assert "checkpoints" in str(error)
        assert error.logical_model == "custom_model"

    def test_error_details(self):
        """Test that errors include details dict."""
        error = MissingNodeError(
            logical_node="test",
            attempted_aliases=["Test"],
        )

        assert "logical_node" in error.details
        assert error.details["logical_node"] == "test"
