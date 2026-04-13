"""Model mapping and registry for resolving logical models to actual filenames."""

from typing import Dict, List, Optional, Set
from pathlib import Path
import os


class ModelMapping:
    """Maps logical model identifiers to actual filenames.

    Supports multiple resolution strategies:
    1. Exact match from registry
    2. Pattern matching (e.g., "sdxl_base" matches "sd_xl_base_1.0.safetensors")
    3. Fallback to default if configured
    """

    def __init__(
        self,
        logical_id: str,
        model_type: str,
        preferred_filename: Optional[str] = None,
        fallback_patterns: Optional[List[str]] = None,
        required: bool = True,
    ):
        self.logical_id = logical_id
        self.model_type = model_type
        self.preferred_filename = preferred_filename
        self.fallback_patterns = fallback_patterns or []
        self.required = required


class ModelRegistry:
    """Registry for model mappings with resolution capabilities."""

    # Default model mappings - can be customized per installation
    DEFAULT_MAPPINGS: Dict[str, Dict[str, str]] = {
        "checkpoints": {
            "sdxl_base": "sd_xl_base_1.0.safetensors",
            "sdxl_refiner": "sd_xl_refiner_1.0.safetensors",
            "sd_1_5": "v1-5-pruned-emaonly.safetensors",
        },
        "sams": {
            "sam_vit_h": "sam_vit_h_4b8939.pth",
            "sam_vit_l": "sam_vit_l_0b3195.pth",
            "sam_vit_b": "sam_vit_b_01ec64.pth",
        },
        "clip_vision": {
            "clip_vision_h": "clip_vision_vit_h.safetensors",
            "clip_vision_g": "clip_vision_vit_g.safetensors",
        },
        "text_encoders": {
            "t5_xxl_encoder": "t5/t5xxl_fp8_e4m3fn.safetensors",
        },
        "diffusion_models": {
            "cogvideox_5b_i2v": "CogVideoX_1_0_5b_I2V_bf16.safetensors",
            "cogvideox_5b": "cogvideox_5b.safetensors",
        },
        "vae": {
            "cogvideox_vae": "cogvideox_vae_bf16.safetensors",
        },
        "loras": {
            "product_photography": "product_photography_v1.safetensors",
        },
    }

    def __init__(
        self,
        model_paths: Optional[Dict[str, str]] = None,
        allow_pattern_matching: bool = True,
    ):
        """Initialize model registry.

        Args:
            model_paths: Dict mapping model types to directory paths
            allow_pattern_matching: Whether to allow fuzzy pattern matching
        """
        self.mappings: Dict[str, Dict[str, str]] = {
            category: dict(models) for category, models in self.DEFAULT_MAPPINGS.items()
        }
        self.model_paths = model_paths or {}
        self.allow_pattern_matching = allow_pattern_matching
        self._available_cache: Dict[str, Set[str]] = {}

    def register_model(self, logical_id: str, model_type: str, filename: str):
        """Register a model mapping."""
        if model_type not in self.mappings:
            self.mappings[model_type] = {}
        self.mappings[model_type][logical_id] = filename

    def resolve(self, logical_id: str, model_type: str) -> Optional[str]:
        """Resolve a logical model ID to an actual filename.

        Resolution order:
        1. Direct lookup in registry
        2. Pattern matching if enabled
        3. Return logical_id as-is (assume it's already a filename)

        Args:
            logical_id: Logical model identifier
            model_type: Type of model (checkpoints, loras, etc.)

        Returns:
            Resolved filename or None if not found
        """
        # Direct lookup
        type_mappings = self.mappings.get(model_type, {})
        if logical_id in type_mappings:
            return type_mappings[logical_id]

        # Pattern matching
        if self.allow_pattern_matching:
            # Try to find a model that contains the logical_id
            available = self._get_available_models(model_type)
            if available:
                # Exact match first
                if logical_id in available:
                    return logical_id

                # Pattern match
                logical_lower = logical_id.lower().replace("_", "")
                for model in available:
                    model_lower = model.lower().replace("_", "").replace("-", "")
                    if logical_lower in model_lower or model_lower in logical_lower:
                        return model

        # Assume logical_id is already a filename
        return logical_id

    def _get_available_models(self, model_type: str) -> Set[str]:
        """Get cached list of available models for a type."""
        if model_type in self._available_cache:
            return self._available_cache[model_type]

        # Try to scan directory if path is configured
        if model_type in self.model_paths:
            path = Path(self.model_paths[model_type])
            if path.exists():
                models = {
                    f.name
                    for f in path.iterdir()
                    if f.is_file()
                    and f.suffix in {".safetensors", ".ckpt", ".pth", ".bin"}
                }
                self._available_cache[model_type] = models
                return models

        return set()

    def list_models(self, model_type: str) -> List[str]:
        """List available models for a type.

        Returns:
            List of logical model IDs and available filenames
        """
        result = set()

        # Add registered mappings
        if model_type in self.mappings:
            result.update(self.mappings[model_type].keys())

        # Add available files
        available = self._get_available_models(model_type)
        result.update(available)

        return sorted(result)

    def set_model_path(self, model_type: str, path: str):
        """Set the directory path for a model type."""
        self.model_paths[model_type] = path
        # Invalidate cache for this type
        if model_type in self._available_cache:
            del self._available_cache[model_type]

    def scan_available_models(self, model_dirs: Dict[str, str]):
        """Scan directories and populate available model cache.

        Args:
            model_dirs: Dict mapping model types to directory paths
        """
        for model_type, path_str in model_dirs.items():
            path = Path(path_str)
            if path.exists():
                models = {
                    f.name
                    for f in path.iterdir()
                    if f.is_file()
                    and f.suffix in {".safetensors", ".ckpt", ".pth", ".bin"}
                }
                self._available_cache[model_type] = models
                self.model_paths[model_type] = path_str
