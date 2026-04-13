"""
ComfyUI discovery and capability foundation for portability MVP.

This package provides:
- Discovery client for querying ComfyUI backend capabilities
- Capability analysis for evaluating workflow compatibility
- Workflow manifest system for portable workflow definitions
- Node alias mappings for handling node name drift
"""

from app.services.comfyui.discovery import ComfyUIDiscoveryClient
from app.services.comfyui.capability import CapabilityAnalyzer, CompatibilityResult
from app.services.comfyui.manifest import WorkflowManifest, WorkflowManifestLoader
from app.services.comfyui.types import NodeSpec, ModelRequirement, OutputSpec

__all__ = [
    "ComfyUIDiscoveryClient",
    "CapabilityAnalyzer",
    "CompatibilityResult",
    "WorkflowManifest",
    "WorkflowManifestLoader",
    "NodeSpec",
    "ModelRequirement",
    "OutputSpec",
]