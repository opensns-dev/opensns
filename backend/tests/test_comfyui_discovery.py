"""
Tests for ComfyUI discovery and capability analysis.

These tests use mock object_info payloads to avoid requiring a live ComfyUI server.
"""

import pytest
from typing import Dict, Any

from app.services.comfyui.discovery import ComfyUIDiscoveryClient
from app.services.comfyui.types import (
    ObjectInfoResponse,
    NodeSpec,
    NodeInputSpec,
    NodeOutputSpec,
    InputType,
)
from app.services.comfyui.aliases import (
    build_alias_index,
    get_canonical_name,
    get_all_known_names_for,
    ALL_ALIASES,
)
from app.services.comfyui.capability import CapabilityAnalyzer, CompatibilityStatus
from app.services.comfyui.manifest import WorkflowManifest, NodeRequirement


# Sample mock object_info responses for testing

MOCK_OBJECT_INFO_MINIMAL: Dict[str, Any] = {
    "CheckpointLoaderSimple": {
        "input": {
            "required": {
                "ckpt_name": [["model1.safetensors", "model2.safetensors"], {}]
            }
        },
        "output": ["MODEL", "CLIP", "VAE"],
        "output_name": ["MODEL", "CLIP", "VAE"],
        "output_is_list": [False, False, False],
        "category": "loaders",
        "display_name": "Load Checkpoint",
    },
    "LoadImage": {
        "input": {"required": {"image": [["image1.png", "image2.png"], {}]}},
        "output": ["IMAGE", "MASK"],
        "output_name": ["IMAGE", "MASK"],
        "output_is_list": [False, False],
        "category": "image",
        "display_name": "Load Image",
    },
    "KSampler": {
        "input": {
            "required": {
                "model": ["MODEL", {}],
                "positive": ["CONDITIONING", {}],
                "negative": ["CONDITIONING", {}],
                "latent_image": ["LATENT", {}],
                "seed": ["INT", {"default": 0, "min": 0, "max": 4294967295}],
                "steps": ["INT", {"default": 20, "min": 1, "max": 10000}],
                "cfg": ["FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0}],
                "sampler_name": [["euler", "euler_ancestral", "dpmpp_2m"], {}],
                "scheduler": [["normal", "karras", "simple"], {}],
                "denoise": ["FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}],
            }
        },
        "output": ["LATENT"],
        "output_name": ["LATENT"],
        "output_is_list": [False],
        "category": "sampling",
        "display_name": "KSampler",
    },
}

MOCK_OBJECT_INFO_WITH_ALIASES: Dict[str, Any] = {
    # Using an alias name instead of canonical
    "SAMLoader": {
        "input": {"required": {"model_name": [["sam_vit_h.pth", "sam_vit_l.pth"], {}]}},
        "output": ["SAM_MODEL"],
        "output_name": ["SAM_MODEL"],
        "output_is_list": [False],
        "category": "segment_anything",
        "display_name": "SAM Model Loader",
    },
    # Using alternative CogVideoX name
    "CogVideo Loader": {
        "input": {"required": {"model_name": [["cogvideox_5b_i2v.safetensors"], {}]}},
        "output": ["COGVIDEO_MODEL", "CLIP", "VAE"],
        "output_name": ["MODEL", "CLIP", "VAE"],
        "output_is_list": [False, False, False],
        "category": "CogVideo",
        "display_name": "CogVideo Loader",
    },
    **MOCK_OBJECT_INFO_MINIMAL,
}


class TestComfyUIDiscoveryClient:
    """Tests for the discovery client."""

    def test_parse_node_spec_basic(self):
        """Test parsing a basic node specification."""
        client = ComfyUIDiscoveryClient()
        node_data = MOCK_OBJECT_INFO_MINIMAL["CheckpointLoaderSimple"]

        spec = client._parse_node_spec("CheckpointLoaderSimple", node_data)

        assert spec.class_name == "CheckpointLoaderSimple"
        assert spec.category == "loaders"
        assert spec.display_name == "Load Checkpoint"
        assert len(spec.inputs) == 1
        assert spec.inputs[0].name == "ckpt_name"
        assert spec.inputs[0].type == InputType.COMBO
        assert spec.inputs[0].options == ["model1.safetensors", "model2.safetensors"]
        assert len(spec.outputs) == 3
        assert spec.outputs[0].name == "MODEL"

    def test_parse_node_spec_with_config(self):
        """Test parsing a node with configured inputs."""
        client = ComfyUIDiscoveryClient()
        node_data = MOCK_OBJECT_INFO_MINIMAL["KSampler"]

        spec = client._parse_node_spec("KSampler", node_data)

        assert spec.class_name == "KSampler"
        assert (
            len(spec.inputs) == 10
        )  # All required inputs (model, positive, negative, latent_image, seed, steps, cfg, sampler_name, scheduler, denoise)

        # Check seed input has config
        seed_input = next(inp for inp in spec.inputs if inp.name == "seed")
        assert seed_input.type == InputType.INT
        assert seed_input.default == 0
        assert seed_input.min_value == 0
        assert seed_input.max_value == 4294967295

        # Check sampler_name is COMBO
        sampler_input = next(inp for inp in spec.inputs if inp.name == "sampler_name")
        assert sampler_input.type == InputType.COMBO
        assert "euler" in sampler_input.options

    def test_parse_input_spec_string_only(self):
        """Test parsing simple string input spec."""
        client = ComfyUIDiscoveryClient()
        spec = client._parse_input_spec("test_input", "MODEL", required=True)

        assert spec.name == "test_input"
        assert spec.type == "MODEL"
        assert spec.required is True

    def test_parse_input_spec_combo(self):
        """Test parsing COMBO type input spec."""
        client = ComfyUIDiscoveryClient()
        spec = client._parse_input_spec(
            "test_combo",
            [["option1", "option2"], {"default": "option1"}],
            required=True,
        )

        assert spec.name == "test_combo"
        assert spec.type == InputType.COMBO
        assert spec.options == ["option1", "option2"]
        assert spec.default == "option1"


class TestAliasResolution:
    """Tests for node alias resolution."""

    def test_build_alias_index(self):
        """Test building the alias lookup index."""
        index = build_alias_index()

        # Canonical should map to itself
        assert index["SAMModelLoader"] == "SAMModelLoader"

        # Aliases should map to canonical
        assert index["SAMLoader"] == "SAMModelLoader"
        assert index["SAM Model Loader"] == "SAMModelLoader"

    def test_get_canonical_name(self):
        """Test resolving aliases to canonical names."""
        # Canonical returns itself
        assert get_canonical_name("SAMModelLoader") == "SAMModelLoader"

        # Alias resolves to canonical
        assert get_canonical_name("SAMLoader") == "SAMModelLoader"
        assert get_canonical_name("SAM Model Loader") == "SAMModelLoader"

        # Unknown name returns as-is
        assert get_canonical_name("UnknownNode") == "UnknownNode"

    def test_get_all_known_names(self):
        """Test getting all known names for a canonical node."""
        names = get_all_known_names_for("SAMModelLoader")

        assert "SAMModelLoader" in names
        assert "SAMLoader" in names
        assert "SAM Model Loader" in names


class TestCapabilityAnalyzer:
    """Tests for the capability analyzer."""

    def test_check_compatibility_compatible(self):
        """Test checking compatibility with all required nodes present."""
        # Build object info from mock
        nodes = {}
        client = ComfyUIDiscoveryClient()
        for class_name, node_data in MOCK_OBJECT_INFO_MINIMAL.items():
            nodes[class_name] = client._parse_node_spec(class_name, node_data)

        object_info = ObjectInfoResponse(nodes=nodes)
        analyzer = CapabilityAnalyzer(object_info)

        # Create a simple manifest
        manifest = WorkflowManifest(
            workflow_id="test_workflow",
            workflow_type="test",
            name="Test Workflow",
            required_nodes=[
                NodeRequirement(node_class="CheckpointLoaderSimple", required=True),
                NodeRequirement(node_class="KSampler", required=True),
            ],
        )

        result = analyzer.check_compatibility(manifest)

        assert result.is_compatible is True
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert len(result.missing_nodes) == 0

    def test_check_compatibility_missing_nodes(self):
        """Test checking compatibility with missing required nodes."""
        nodes = {}
        client = ComfyUIDiscoveryClient()
        for class_name, node_data in MOCK_OBJECT_INFO_MINIMAL.items():
            nodes[class_name] = client._parse_node_spec(class_name, node_data)

        object_info = ObjectInfoResponse(nodes=nodes)
        analyzer = CapabilityAnalyzer(object_info)

        # Create a manifest with a missing node
        manifest = WorkflowManifest(
            workflow_id="test_workflow",
            workflow_type="test",
            name="Test Workflow",
            required_nodes=[
                NodeRequirement(node_class="CheckpointLoaderSimple", required=True),
                NodeRequirement(node_class="NonExistentNode", required=True),
            ],
        )

        result = analyzer.check_compatibility(manifest)

        assert result.is_compatible is False
        assert result.status == CompatibilityStatus.MISSING_NODES
        assert len(result.missing_nodes) == 1
        assert result.missing_nodes[0].canonical_name == "NonExistentNode"

    def test_check_compatibility_with_aliases(self):
        """Test that aliases are properly resolved during compatibility check."""
        nodes = {}
        client = ComfyUIDiscoveryClient()
        for class_name, node_data in MOCK_OBJECT_INFO_WITH_ALIASES.items():
            nodes[class_name] = client._parse_node_spec(class_name, node_data)

        object_info = ObjectInfoResponse(nodes=nodes)
        analyzer = CapabilityAnalyzer(object_info)

        # Request canonical name but backend has alias
        manifest = WorkflowManifest(
            workflow_id="test_workflow",
            workflow_type="test",
            name="Test Workflow",
            required_nodes=[
                NodeRequirement(
                    node_class="SAMModelLoader", required=True
                ),  # Canonical
            ],
        )

        result = analyzer.check_compatibility(manifest)

        # Should be compatible because SAMLoader is an alias for SAMModelLoader
        assert result.is_compatible is True
        assert len(result.missing_nodes) == 0

    def test_is_node_available(self):
        """Test checking if a specific node is available."""
        nodes = {}
        client = ComfyUIDiscoveryClient()
        for class_name, node_data in MOCK_OBJECT_INFO_MINIMAL.items():
            nodes[class_name] = client._parse_node_spec(class_name, node_data)

        object_info = ObjectInfoResponse(nodes=nodes)
        analyzer = CapabilityAnalyzer(object_info)

        assert analyzer.is_node_available("CheckpointLoaderSimple") is True
        assert analyzer.is_node_available("NonExistentNode") is False

    def test_get_node_spec(self):
        """Test retrieving node specification."""
        nodes = {}
        client = ComfyUIDiscoveryClient()
        for class_name, node_data in MOCK_OBJECT_INFO_MINIMAL.items():
            nodes[class_name] = client._parse_node_spec(class_name, node_data)

        object_info = ObjectInfoResponse(nodes=nodes)
        analyzer = CapabilityAnalyzer(object_info)

        spec = analyzer.get_node_spec("CheckpointLoaderSimple")
        assert spec is not None
        assert spec.class_name == "CheckpointLoaderSimple"

        # Non-existent node returns None
        assert analyzer.get_node_spec("NonExistentNode") is None


class TestWorkflowManifest:
    """Tests for workflow manifest loading."""

    def test_manifest_loading(self):
        """Test loading a manifest from file."""
        from app.services.comfyui.manifest import load_manifest

        # Load the SDXL background replace manifest
        manifest = load_manifest("sdxl_background_replace_v1")

        assert manifest.workflow_id == "sdxl_background_replace_v1"
        assert manifest.workflow_type == "image"
        assert len(manifest.required_nodes) > 0
        assert len(manifest.required_models) > 0
        assert len(manifest.expected_outputs) > 0

    def test_cogvideo_manifest_loading(self):
        """Test loading the CogVideoX manifest."""
        from app.services.comfyui.manifest import load_manifest

        manifest = load_manifest("cogvideox_i2v_v1")

        assert manifest.workflow_id == "cogvideox_i2v_v1"
        assert manifest.workflow_type == "video"
        assert len(manifest.required_nodes) > 0

        # Check for CogVideoX specific nodes
        node_classes = [n.node_class for n in manifest.required_nodes]
        assert "CogVideoXModelLoader" in node_classes
        assert "CogVideoXSampler" in node_classes

    def test_list_manifests(self):
        """Test listing available manifests."""
        from app.services.comfyui.manifest import list_manifests

        manifests = list_manifests()

        assert "sdxl_background_replace_v1" in manifests
        assert "cogvideox_i2v_v1" in manifests
