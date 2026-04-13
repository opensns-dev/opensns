"""
Core types for ComfyUI discovery and workflow manifests.
"""

from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field
from enum import Enum


class InputType(str, Enum):
    """ComfyUI input types."""

    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    IMAGE = "IMAGE"
    LATENT = "LATENT"
    MASK = "MASK"
    MODEL = "MODEL"
    CLIP = "CLIP"
    VAE = "VAE"
    CONDITIONING = "CONDITIONING"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    COMBO = "COMBO"  # Dropdown/enum values


class NodeInputSpec(BaseModel):
    """Specification for a single node input."""

    name: str
    type: Union[InputType, str]  # str for custom types
    required: bool = True
    default: Optional[Any] = None
    # For COMBO type, the list of valid options
    options: Optional[List[str]] = None
    # For primitive types, min/max constraints
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


class NodeOutputSpec(BaseModel):
    """Specification for a single node output."""

    name: str
    type: Union[InputType, str]
    # Is this the primary output that consumers typically use
    is_primary: bool = False


class NodeSpec(BaseModel):
    """
    Specification for a ComfyUI node type.

    This represents the schema of a node class as returned by /object_info.
    """

    class_name: str = Field(..., description="The ComfyUI class_type name")
    category: str = Field(..., description="Category in the ComfyUI menu")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Node description")
    inputs: List[NodeInputSpec] = Field(default_factory=list)
    outputs: List[NodeOutputSpec] = Field(default_factory=list)
    output_is_list: List[bool] = Field(default_factory=list)
    output_name: Optional[List[str]] = Field(None)
    # Python module path for the node
    python_module: Optional[str] = None


class ModelType(str, Enum):
    """Types of models that can be required by workflows."""

    CHECKPOINT = "checkpoint"
    VAE = "vae"
    LORA = "lora"
    CLIP_VISION = "clip_vision"
    CONTROLNET = "controlnet"
    IPADAPTER = "ipadapter"
    UPSCALE_MODEL = "upscale_model"
    SAM_MODEL = "sam_model"
    VIDEO_MODEL = "video_model"


class ModelRequirement(BaseModel):
    """
    A model required by a workflow.

    Uses logical identifiers that can be mapped to actual filenames
    on different ComfyUI installations.
    """

    logical_id: str = Field(
        ..., description="Logical model identifier, e.g., 'sdxl_base_1.0'"
    )
    model_type: ModelType
    # Alternative logical IDs that can satisfy this requirement
    alternatives: List[str] = Field(default_factory=list)
    # Whether this model is strictly required or can use a fallback
    required: bool = True
    # Human-readable description of what this model is used for
    description: Optional[str] = None


class OutputSpec(BaseModel):
    """
    Specification for expected workflow outputs.
    """

    output_type: str = Field(
        ..., description="Type of output: 'image', 'video', 'latent', etc."
    )
    # Node class type that produces this output
    source_node_class: str
    # Output slot index or name
    source_output_index: Union[int, str] = 0
    # Expected filename pattern (for detection)
    filename_pattern: Optional[str] = None
    # Whether this is the primary output
    is_primary: bool = False


class NodeAlias(BaseModel):
    """
    Mapping for node name drift - different names for the same logical node.

    This handles cases where:
    - Custom nodes change names between versions
    - Different implementations exist (e.g., segment-anything vs SAM)
    - Wrapper nodes vs native nodes
    """

    canonical_name: str = Field(..., description="The primary/reference name")
    aliases: List[str] = Field(
        default_factory=list, description="Alternative names for the same node"
    )
    # If True, the aliases are considered equivalent (same inputs/outputs)
    # If False, minor adaptations may be needed
    fully_equivalent: bool = True
    # Notes about differences between aliases
    compatibility_notes: Optional[str] = None


class ObjectInfoResponse(BaseModel):
    """
    Parsed response from ComfyUI's /object_info endpoint.
    """

    nodes: Dict[str, NodeSpec] = Field(default_factory=dict)
    # Raw response for debugging
    raw_response: Optional[Dict[str, Any]] = None


class SystemStatsResponse(BaseModel):
    """
    Parsed response from ComfyUI's /system_stats endpoint.
    """

    # System info
    comfyui_version: Optional[str] = None
    python_version: Optional[str] = None
    # Device info
    devices: List[Dict[str, Any]] = Field(default_factory=list)
    # Available memory per device
    memory: Dict[str, Any] = Field(default_factory=dict)
    # Raw response for debugging
    raw_response: Optional[Dict[str, Any]] = None
