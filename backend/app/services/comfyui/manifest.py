"""
Workflow manifest system for portable ComfyUI workflows.

Workflow manifests define:
- Required nodes (with logical identifiers)
- Required models (with logical identifiers)
- Expected outputs
- Workflow metadata

Manifests are stored as JSON files and can be loaded dynamically.
This allows adapters to use portable workflow definitions instead of
hardcoded dictionaries.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from app.services.comfyui.types import NodeSpec, ModelRequirement, OutputSpec


class NodeRequirement(BaseModel):
    """
    A node required by a workflow.
    
    Uses canonical node names that can be resolved to actual
    ComfyUI class names via the alias system.
    """
    # Canonical node name (e.g., "CheckpointLoaderSimple")
    node_class: str = Field(..., description="Canonical node class name")
    # Whether this node is strictly required
    required: bool = True
    # Minimum required inputs and their types (for schema validation)
    required_inputs: Dict[str, str] = Field(default_factory=dict)
    # Description of what this node is used for
    description: Optional[str] = None


class WorkflowManifest(BaseModel):
    """
    A portable workflow manifest for ComfyUI.
    
    This defines what a workflow needs to run, without hardcoding
    specific node class names, model filenames, or installation-specific
    details.
    
    Example:
        {
            "manifest_version": "1.0",
            "workflow_id": "sdxl_background_replace_v1",
            "workflow_type": "image",
            "name": "SDXL Background Replacement",
            "description": "Replaces background of product images using SDXL inpainting",
            "required_nodes": [...],
            "required_models": [...],
            "expected_outputs": [...],
            "parameters": {...}
        }
    """
    manifest_version: str = Field(default="1.0", description="Manifest schema version")
    workflow_id: str = Field(..., description="Unique logical identifier for this workflow")
    workflow_type: str = Field(..., description="Type: 'image', 'video', 'inpaint', etc.")
    
    # Metadata
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Detailed description")
    author: Optional[str] = None
    version: str = "1.0"
    
    # Requirements
    required_nodes: List[NodeRequirement] = Field(
        default_factory=list,
        description="Nodes required by this workflow"
    )
    required_models: List[ModelRequirement] = Field(
        default_factory=list,
        description="Models required by this workflow"
    )
    expected_outputs: List[OutputSpec] = Field(
        default_factory=list,
        description="Expected outputs from this workflow"
    )
    
    # Runtime parameters (default values, can be overridden)
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default parameters for the workflow"
    )
    
    # Optional: Reference to the actual workflow JSON file
    # This allows loading the executable workflow separately
    workflow_file: Optional[str] = Field(
        None,
        description="Path to the executable workflow JSON (relative to manifest)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "manifest_version": "1.0",
                "workflow_id": "sdxl_background_replace_v1",
                "workflow_type": "image",
                "name": "SDXL Background Replacement",
                "description": "Replaces background using SDXL inpainting",
                "required_nodes": [
                    {"node_class": "LoadImageBase64", "required": True},
                    {"node_class": "CheckpointLoaderSimple", "required": True},
                    {"node_class": "SAMModelLoader", "required": True},
                ],
                "required_models": [
                    {
                        "logical_id": "sdxl_base_1.0",
                        "model_type": "checkpoint",
                        "required": True
                    }
                ],
                "expected_outputs": [
                    {
                        "output_type": "image",
                        "source_node_class": "SaveImage",
                        "is_primary": True
                    }
                ]
            }
        }


class WorkflowManifestLoader:
    """
    Loader for workflow manifests from JSON files.
    """
    
    def __init__(self, manifests_dir: Optional[Path] = None):
        """
        Initialize the loader.
        
        Args:
            manifests_dir: Directory containing manifest JSON files.
                          Defaults to the 'manifests' subdirectory of this module.
        """
        if manifests_dir is None:
            manifests_dir = Path(__file__).parent / "manifests"
        self.manifests_dir = Path(manifests_dir)
    
    def load_manifest(self, manifest_id: str) -> WorkflowManifest:
        """
        Load a manifest by its ID.
        
        Args:
            manifest_id: The workflow_id or filename (without .json extension)
            
        Returns:
            Loaded WorkflowManifest
            
        Raises:
            FileNotFoundError: If the manifest file doesn't exist
            ValueError: If the JSON is invalid
        """
        # Try with .json extension if not provided
        if not manifest_id.endswith(".json"):
            filename = f"{manifest_id}.json"
        else:
            filename = manifest_id
        
        filepath = self.manifests_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Manifest not found: {filepath}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return WorkflowManifest(**data)
    
    def load_manifest_from_file(self, filepath: Union[str, Path]) -> WorkflowManifest:
        """
        Load a manifest from a specific file path.
        
        Args:
            filepath: Path to the JSON manifest file
            
        Returns:
            Loaded WorkflowManifest
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WorkflowManifest(**data)
    
    def list_manifests(self) -> List[str]:
        """
        List all available manifest IDs.
        
        Returns:
            List of manifest IDs (filenames without .json extension)
        """
        if not self.manifests_dir.exists():
            return []
        
        manifests = []
        for filepath in self.manifests_dir.glob("*.json"):
            manifests.append(filepath.stem)
        return sorted(manifests)
    
    def save_manifest(
        self, manifest: WorkflowManifest, filepath: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Save a manifest to a JSON file.
        
        Args:
            manifest: The manifest to save
            filepath: Optional specific path. If None, saves to manifests_dir
                     using the workflow_id as filename.
        """
        if filepath is None:
            filepath = self.manifests_dir / f"{manifest.workflow_id}.json"
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)


# Singleton loader instance for convenience
default_loader = WorkflowManifestLoader()


def load_manifest(manifest_id: str) -> WorkflowManifest:
    """Load a manifest using the default loader."""
    return default_loader.load_manifest(manifest_id)


def list_manifests() -> List[str]:
    """List all manifests using the default loader."""
    return default_loader.list_manifests()
