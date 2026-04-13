"""ComfyUI discovery and node alias resolution."""

import httpx
from typing import Dict, List, Optional, Set
from functools import lru_cache
import time


class ComfyUIDiscovery:
    """Discovers available nodes and capabilities from a ComfyUI instance."""

    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url.rstrip("/")
        self._node_cache: Optional[Dict[str, Dict]] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 300  # 5 minutes

    async def fetch_object_info(self) -> Dict[str, Dict]:
        """Fetch available node types from ComfyUI.

        Returns:
            Dict mapping node class names to their metadata
        """
        if (
            self._node_cache is not None
            and (time.time() - self._cache_timestamp) < self._cache_ttl
        ):
            return self._node_cache

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/object_info")
            response.raise_for_status()
            result: Dict[str, Dict] = response.json()
            self._node_cache = result
            self._cache_timestamp = time.time()
            return result

    def invalidate_cache(self):
        """Clear the node cache to force fresh discovery."""
        self._node_cache = None
        self._cache_timestamp = 0

    async def get_available_nodes(self) -> List[str]:
        """Get list of available node class names."""
        info = await self.fetch_object_info()
        return list(info.keys())

    async def has_node(self, class_name: str) -> bool:
        """Check if a specific node class is available."""
        available = await self.get_available_nodes()
        return class_name in available

    async def get_node_info(self, class_name: str) -> Optional[Dict]:
        """Get metadata for a specific node type."""
        info = await self.fetch_object_info()
        return info.get(class_name)


class NodeAliasResolver:
    """Resolves logical node types to actual ComfyUI class names.

    Maintains a mapping of logical node types to lists of possible
    actual class names, trying them in priority order.
    """

    # Default alias mappings - can be extended
    DEFAULT_ALIASES: Dict[str, List[str]] = {
        # Image loading
        "load_image": ["LoadImage", "Load Image"],
        "load_image_base64": ["LoadImageBase64", "Load Image (Base64)"],
        # Model loading
        "checkpoint_loader": [
            "CheckpointLoaderSimple",
            "CheckpointLoader",
            "Load Checkpoint",
        ],
        "clip_loader": ["CLIPLoader", "Load CLIP"],
        "clip_vision_loader": ["CLIPVisionLoader", "CLIP Vision Loader"],
        "sam_loader": [
            "SAMModelLoader",
            "SAMModelLoader (segment anything)",
            "SAM Model Loader",
        ],
        # Conditioning
        "clip_encode": ["CLIPTextEncode", "CLIP Text Encode"],
        "inpaint_conditioning": [
            "InpaintModelConditioning",
            "Inpaint Model Conditioning",
        ],
        # Sampling
        "ksampler": ["KSampler", "KSamplerAdvanced"],
        # VAE
        "vae_decode": ["VAEDecode", "VAE Decode"],
        "vae_encode": ["VAEEncode", "VAE Encode"],
        # Image operations
        "image_composite_masked": ["ImageCompositeMasked", "Image Composite Masked"],
        "image_scale": ["ImageScale", "Image Scale"],
        "repeat_latent_batch": ["RepeatLatentBatch", "Repeat Latent Batch"],
        "save_image": ["SaveImage", "Save Image"],
        "empty_latent_image": ["EmptyLatentImage", "Empty Latent Image"],
        # Segmentation
        "grounding_dino_sam": [
            "GroundingDinoSAMSegment",
            "GroundingDinoSAMSegment (segment anything)",
            "GroundingDINO SAM Segment",
        ],
        # CogVideoX nodes
        "cogvideo_image_encode": [
            "CogVideoImageEncode",
            "CogVideoXImageEncode",
            "CogVideo Image Encode",
            "CogVideoX Image Encode",
        ],
        "cogvideo_text_encode": [
            "CogVideoTextEncode",
            "CogVideoXTextEncode",
            "CogVideo Text Encode",
            "CogVideoX Text Encode",
        ],
        "cogvideo_model_loader": [
            "DownloadAndLoadCogVideoModel",
            "CogVideoXModelLoader",
            "CogVideo Model Loader",
            "CogVideoX Model Loader",
        ],
        "cogvideo_sampler": [
            "CogVideoSampler",
            "CogVideoXSampler",
            "CogVideo Sampler",
            "CogVideoX Sampler",
        ],
        "cogvideo_decode": [
            "CogVideoDecode",
            "CogVideoXDecode",
            "CogVideo Decode",
            "CogVideoX Decode",
        ],
        # Video
        "video_combine": ["VHS_VideoCombine", "Video Combine", "VHS VideoCombine"],
        "cogvideo_vae_loader": ["CogVideoXVAELoader"],
        # AnimateDiff standard
        "animatediff_loader": [
            "ADE_LoadAnimateDiffModel",
            "Load AnimateDiff Model",
        ],
        "animatediff_apply": [
            "ADE_ApplyAnimateDiffModel",
            "Apply AnimateDiff Model",
        ],
        "use_evolved_sampling": [
            "ADE_UseEvolvedSampling",
            "Use Evolved Sampling",
        ],
        # AnimateLCM-I2V (legacy, MPS-incompatible)
        "animatelcm_i2v_loader": [
            "ADE_LoadAnimateLCMI2VModel",
            "Load AnimateLCM-I2V Model",
        ],
        "animatelcm_i2v_apply": [
            "ADE_ApplyAnimateLCMI2VModel",
            "Apply AnimateLCM-I2V Model",
        ],
    }

    def __init__(self, discovery: Optional[ComfyUIDiscovery] = None):
        self.discovery = discovery
        self._aliases: Dict[str, List[str]] = dict(self.DEFAULT_ALIASES)
        self._available_cache: Optional[Set[str]] = None

    def register_alias(self, logical_type: str, aliases: List[str]):
        """Register or update aliases for a logical node type."""
        self._aliases[logical_type] = aliases

    def get_aliases(self, logical_type: str) -> List[str]:
        """Get the list of aliases for a logical node type."""
        return self._aliases.get(logical_type, [logical_type])

    def resolve(
        self, logical_type: str, priority: Optional[List[str]] = None
    ) -> Optional[str]:
        """Resolve a logical node type to an available class name.

        Args:
            logical_type: The logical node type (e.g., 'load_image')
            priority: Optional priority list of class names to try first

        Returns:
            The first available class name, or None if none found
        """
        # Build candidate list: priority first, then registered aliases, then logical type itself
        candidates = []
        if priority:
            candidates.extend(priority)
        candidates.extend(self.get_aliases(logical_type))
        if logical_type not in candidates:
            candidates.append(logical_type)

        # Remove duplicates while preserving order
        seen = set()
        candidates = [c for c in candidates if not (c in seen or seen.add(c))]

        # If cache is populated, check availability against cache
        if self._available_cache is not None:
            for candidate in candidates:
                if candidate in self._available_cache:
                    return candidate
            return None
        elif self.discovery:
            # Discovery exists but cache not populated - can't verify availability
            # Return None to indicate resolution failed without cache
            return None
        else:
            # No discovery and no cache - return first candidate (best effort)
            return candidates[0] if candidates else None

    async def resolve_with_discovery(
        self, logical_type: str, priority: Optional[List[str]] = None
    ) -> Optional[str]:
        """Resolve with async discovery check.

        Args:
            logical_type: The logical node type
            priority: Optional priority list

        Returns:
            First available class name, or None if none found
        """
        if not self.discovery:
            return self.resolve(logical_type, priority)

        # Update available cache
        available = await self.discovery.get_available_nodes()
        self._available_cache = set(available)

        return self.resolve(logical_type, priority)

    def get_available_nodes(self) -> Optional[List[str]]:
        """Get cached list of available nodes if discovery is configured."""
        if self._available_cache is not None:
            return list(self._available_cache)
        return None

    async def check_compatibility(
        self, logical_types: List[str]
    ) -> Dict[str, Optional[str]]:
        """Check compatibility for multiple logical node types.

        Returns:
            Dict mapping logical types to resolved class names (None if not available)
        """
        if not self.discovery:
            return {lt: self.resolve(lt) for lt in logical_types}

        available = await self.discovery.get_available_nodes()
        self._available_cache = set(available)

        return {lt: self.resolve(lt) for lt in logical_types}
