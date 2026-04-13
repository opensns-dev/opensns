"""Workflow loader for loading manifests from files or presets."""

import json
from pathlib import Path
from typing import Dict, Optional, Union
from .manifest import WorkflowManifest
from .exceptions import WorkflowValidationError


class WorkflowLoader:
    """Loads workflow manifests from various sources."""

    def __init__(self, manifests_dir: Optional[Path] = None):
        self.manifests_dir = manifests_dir or Path(__file__).parent / "manifests"
        self._presets: Dict[str, WorkflowManifest] = {}
        self._register_builtin_presets()

    def _register_builtin_presets(self):
        """Register built-in workflow manifests."""
        from .manifest import (
            BACKGROUND_REPLACEMENT_MANIFEST,
            TEXT_TO_IMAGE_MANIFEST,
            ANIMATEDIFF_V3_MANIFEST,
        )

        self._presets["background_replacement"] = BACKGROUND_REPLACEMENT_MANIFEST
        self._presets["text_to_image"] = TEXT_TO_IMAGE_MANIFEST
        self._presets["animatediff_v3"] = ANIMATEDIFF_V3_MANIFEST

    def load_from_file(self, path: Union[str, Path]) -> WorkflowManifest:
        """Load a workflow manifest from a JSON file.

        Args:
            path: Path to the JSON manifest file

        Returns:
            Parsed WorkflowManifest

        Raises:
            FileNotFoundError: If file doesn't exist
            WorkflowValidationError: If manifest is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        try:
            return WorkflowManifest(**data)
        except Exception as e:
            raise WorkflowValidationError([str(e)])

    def load_from_json(self, json_str: str) -> WorkflowManifest:
        """Load a workflow manifest from a JSON string.

        Args:
            json_str: JSON string containing the manifest

        Returns:
            Parsed WorkflowManifest
        """
        data = json.loads(json_str)
        try:
            return WorkflowManifest(**data)
        except Exception as e:
            raise WorkflowValidationError([str(e)])

    def get_preset(self, name: str) -> Optional[WorkflowManifest]:
        """Get a built-in preset manifest by name.

        Args:
            name: Preset name (e.g., 'background_replacement')

        Returns:
            The preset manifest or None if not found
        """
        return self._presets.get(name)

    def list_presets(self) -> Dict[str, str]:
        """List available preset names and descriptions.

        Returns:
            Dict mapping preset names to descriptions
        """
        return {name: manifest.description for name, manifest in self._presets.items()}

    def register_preset(self, name: str, manifest: WorkflowManifest):
        """Register a custom preset.

        Args:
            name: Preset name
            manifest: WorkflowManifest to register
        """
        self._presets[name] = manifest

    def save_to_file(
        self,
        manifest: WorkflowManifest,
        path: Union[str, Path],
        overwrite: bool = False,
    ):
        """Save a manifest to a JSON file.

        Args:
            manifest: Manifest to save
            path: Destination path
            overwrite: Whether to overwrite existing file
        """
        path = Path(path)
        if path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {path}")

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)
