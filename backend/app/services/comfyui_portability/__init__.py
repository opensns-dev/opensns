"""ComfyUI Portability Foundation

Provides workflow manifests, node alias resolution, and model mapping
for portable ComfyUI workflows across different installations.
"""

from .manifest import (
    WorkflowManifest,
    NodeDefinition,
    NodeInput,
    NodeOutput,
    WorkflowOutput,
    NodeInputMapping,
    OutputDefinition,
    InputType,
)
from .discovery import ComfyUIDiscovery, NodeAliasResolver
from .model_mapping import ModelRegistry, ModelMapping
from .loader import WorkflowLoader
from .exceptions import (
    ComfyUICompatibilityError,
    MissingNodeError,
    MissingModelError,
    UnsupportedOutputError,
    WorkflowValidationError,
)

__all__ = [
    "WorkflowManifest",
    "NodeDefinition",
    "NodeInput",
    "NodeOutput",
    "WorkflowOutput",
    "NodeInputMapping",
    "OutputDefinition",
    "InputType",
    "ComfyUIDiscovery",
    "NodeAliasResolver",
    "ModelRegistry",
    "ModelMapping",
    "WorkflowLoader",
    "ComfyUICompatibilityError",
    "MissingNodeError",
    "MissingModelError",
    "UnsupportedOutputError",
    "WorkflowValidationError",
]
