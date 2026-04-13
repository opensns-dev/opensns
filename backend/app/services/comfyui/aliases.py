"""
Node alias mappings for handling ComfyUI node name drift.

Different ComfyUI installations, custom node packs, and versions
may use different names for the same logical node. This module
provides canonical mappings so that workflow manifests can use
stable logical identifiers while being compatible with various
backend configurations.
"""

from typing import Dict, List, Optional, Set
from app.services.comfyui.types import NodeAlias


# Known node aliases for segment-anything related nodes
# Different custom node packs use different naming conventions
SEGMENT_ANYTHING_ALIASES: List[NodeAlias] = [
    NodeAlias(
        canonical_name="SAMModelLoader",
        aliases=[
            "SAMModelLoader",
            "SAMLoader",
            "SAM Model Loader",
        ],
        fully_equivalent=True,
        compatibility_notes="Loads Segment Anything model checkpoints",
    ),
    NodeAlias(
        canonical_name="GroundingDinoSAMSegment",
        aliases=[
            "GroundingDinoSAMSegment",
            "GroundingDINO-SAM-Segment",
            "GroundingDINOSAMSegment",
            "GroundingDinoSAMSegment (segment anything)",
        ],
        fully_equivalent=True,
        compatibility_notes="Segments image using GroundingDINO + SAM",
    ),
]

# CogVideoX related nodes
# Multiple wrapper implementations exist with different naming
COGVIDEO_ALIASES: List[NodeAlias] = [
    NodeAlias(
        canonical_name="CogVideoXModelLoader",
        aliases=[
            "CogVideoXModelLoader",
            "CogVideo Loader",
            "CogVideoXLoader",
            "Load CogVideoX Model",
        ],
        fully_equivalent=True,
        compatibility_notes="Loads CogVideoX model for video generation",
    ),
    NodeAlias(
        canonical_name="CogVideoXImageEncode",
        aliases=[
            "CogVideoXImageEncode",
            "CogVideo Image Encode",
            "CogVideoXImageToVideo",
            "CogVideo Image to Video",
        ],
        fully_equivalent=True,
        compatibility_notes="Encodes image for CogVideoX I2V generation",
    ),
    NodeAlias(
        canonical_name="CogVideoXTextEncode",
        aliases=[
            "CogVideoXTextEncode",
            "CogVideo Text Encode",
            "CogVideoX Encode Prompt",
        ],
        fully_equivalent=True,
        compatibility_notes="Encodes text prompt for CogVideoX",
    ),
    NodeAlias(
        canonical_name="CogVideoXSampler",
        aliases=[
            "CogVideoXSampler",
            "CogVideo Sampler",
            "CogVideoX Sample",
        ],
        fully_equivalent=True,
        compatibility_notes="Runs diffusion sampling for CogVideoX",
    ),
    NodeAlias(
        canonical_name="CogVideoXDecode",
        aliases=[
            "CogVideoXDecode",
            "CogVideo Decode",
            "CogVideoX VAE Decode",
        ],
        fully_equivalent=True,
        compatibility_notes="Decodes latents to video frames for CogVideoX",
    ),
]

# Video combining nodes
VIDEO_COMBINE_ALIASES: List[NodeAlias] = [
    NodeAlias(
        canonical_name="VHS_VideoCombine",
        aliases=[
            "VHS_VideoCombine",
            "Video Combine",
            "VideoCombine",
            "Save Video",
        ],
        fully_equivalent=True,
        compatibility_notes="Combines frames into video file",
    ),
]

# Image loading nodes
IMAGE_LOADER_ALIASES: List[NodeAlias] = [
    NodeAlias(
        canonical_name="LoadImage",
        aliases=[
            "LoadImage",
            "Image Load",
            "Load Image",
        ],
        fully_equivalent=True,
    ),
    NodeAlias(
        canonical_name="LoadImageBase64",
        aliases=[
            "LoadImageBase64",
            "Load Image (Base64)",
            "Base64ImageLoader",
        ],
        fully_equivalent=True,
        compatibility_notes="Loads image from base64 string",
    ),
]

# Checkpoint/model loading nodes
CHECKPOINT_LOADER_ALIASES: List[NodeAlias] = [
    NodeAlias(
        canonical_name="CheckpointLoaderSimple",
        aliases=[
            "CheckpointLoaderSimple",
            "Load Checkpoint",
            "CheckpointLoader",
            "Load Diffusion Model",
        ],
        fully_equivalent=True,
    ),
]

# CLIP Vision loading nodes
CLIP_VISION_ALIASES: List[NodeAlias] = [
    NodeAlias(
        canonical_name="CLIPVisionLoader",
        aliases=[
            "CLIPVisionLoader",
            "Load CLIP Vision",
            "CLIP Vision Loader",
        ],
        fully_equivalent=True,
    ),
]

# All aliases combined
ALL_ALIASES: List[NodeAlias] = (
    SEGMENT_ANYTHING_ALIASES
    + COGVIDEO_ALIASES
    + VIDEO_COMBINE_ALIASES
    + IMAGE_LOADER_ALIASES
    + CHECKPOINT_LOADER_ALIASES
    + CLIP_VISION_ALIASES
)


def build_alias_index(aliases: Optional[List[NodeAlias]] = None) -> Dict[str, str]:
    """
    Build a lookup index mapping any alias to its canonical name.
    
    Args:
        aliases: List of NodeAlias mappings. Defaults to ALL_ALIASES.
        
    Returns:
        Dict mapping alias name -> canonical name
    """
    if aliases is None:
        aliases = ALL_ALIASES
    
    index: Dict[str, str] = {}
    for alias_mapping in aliases:
        # Map canonical to itself
        index[alias_mapping.canonical_name] = alias_mapping.canonical_name
        # Map all aliases to canonical
        for alias in alias_mapping.aliases:
            index[alias] = alias_mapping.canonical_name
    return index


def get_canonical_name(
    class_name: str, alias_index: Optional[Dict[str, str]] = None
) -> str:
    """
    Get the canonical name for a node class, resolving aliases.
    
    Args:
        class_name: The node class name from ComfyUI
        alias_index: Pre-built alias index. If None, builds from ALL_ALIASES.
        
    Returns:
        The canonical name if found, otherwise the original class_name
    """
    if alias_index is None:
        alias_index = build_alias_index()
    return alias_index.get(class_name, class_name)


def get_all_known_names_for(
    canonical_name: str, aliases: Optional[List[NodeAlias]] = None
) -> Set[str]:
    """
    Get all known names (canonical + aliases) for a given canonical node name.
    
    Args:
        canonical_name: The canonical node name
        aliases: List of NodeAlias mappings. Defaults to ALL_ALIASES.
        
    Returns:
        Set of all known names for this node
    """
    if aliases is None:
        aliases = ALL_ALIASES
    
    for alias_mapping in aliases:
        if alias_mapping.canonical_name == canonical_name:
            result = set(alias_mapping.aliases)
            result.add(canonical_name)
            return result
    
    return {canonical_name}
