"""
Capability analysis for evaluating workflow compatibility with ComfyUI backends.

This module provides:
- CompatibilityResult: Structured result of compatibility checks
- CapabilityAnalyzer: Analyzes if a workflow can run on a given ComfyUI instance
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.services.comfyui.types import (
    NodeSpec,
    ObjectInfoResponse,
    ModelType,
)
from app.services.comfyui.manifest import WorkflowManifest, NodeRequirement
from app.services.comfyui.aliases import (
    build_alias_index,
    get_canonical_name,
    get_all_known_names_for,
    ALL_ALIASES,
)


class CompatibilityStatus(str, Enum):
    """Status of a compatibility check."""
    COMPATIBLE = "compatible"
    MISSING_NODES = "missing_nodes"
    MISSING_MODELS = "missing_models"
    SCHEMA_MISMATCH = "schema_mismatch"
    INCOMPATIBLE = "incompatible"


@dataclass
class MissingNodeInfo:
    """Information about a missing node."""
    canonical_name: str
    required: bool
    description: Optional[str] = None
    # Alternative names that were also checked
    aliases_checked: List[str] = field(default_factory=list)


@dataclass
class MissingModelInfo:
    """Information about a missing model."""
    logical_id: str
    model_type: ModelType
    required: bool
    description: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)


@dataclass
class SchemaMismatchInfo:
    """Information about a schema mismatch."""
    node_class: str
    input_name: str
    expected_type: str
    actual_type: str
    severity: str = "warning"  # "error" or "warning"


@dataclass
class CompatibilityResult:
    """
    Result of a workflow compatibility check.
    
    This provides detailed information about whether a workflow can
    run on a given ComfyUI backend and what issues exist if not.
    """
    workflow_id: str
    status: CompatibilityStatus
    is_compatible: bool
    
    # Missing items
    missing_nodes: List[MissingNodeInfo] = field(default_factory=list)
    missing_models: List[MissingModelInfo] = field(default_factory=list)
    
    # Schema issues
    schema_mismatches: List[SchemaMismatchInfo] = field(default_factory=list)
    
    # Available items (for reference)
    available_nodes: List[str] = field(default_factory=list)
    available_models: Dict[ModelType, List[str]] = field(default_factory=dict)
    
    # Summary message
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary for JSON serialization."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "is_compatible": self.is_compatible,
            "missing_nodes": [
                {
                    "canonical_name": n.canonical_name,
                    "required": n.required,
                    "description": n.description,
                    "aliases_checked": n.aliases_checked,
                }
                for n in self.missing_nodes
            ],
            "missing_models": [
                {
                    "logical_id": m.logical_id,
                    "model_type": m.model_type.value,
                    "required": m.required,
                    "description": m.description,
                    "alternatives": m.alternatives,
                }
                for m in self.missing_models
            ],
            "schema_mismatches": [
                {
                    "node_class": s.node_class,
                    "input_name": s.input_name,
                    "expected_type": s.expected_type,
                    "actual_type": s.actual_type,
                    "severity": s.severity,
                }
                for s in self.schema_mismatches
            ],
            "available_nodes": self.available_nodes,
            "available_models": {
                k.value: v for k, v in self.available_models.items()
            },
            "message": self.message,
        }


class CapabilityAnalyzer:
    """
    Analyzes ComfyUI backend capabilities against workflow requirements.
    
    This class takes the parsed /object_info response and evaluates
    whether a workflow manifest can be executed on that backend.
    """
    
    def __init__(self, object_info: ObjectInfoResponse):
        """
        Initialize the analyzer with backend capabilities.
        
        Args:
            object_info: Parsed response from ComfyUI's /object_info endpoint
        """
        self.object_info = object_info
        self.alias_index = build_alias_index(ALL_ALIASES)
        
        # Build canonical node availability map
        self._available_canonical: Dict[str, str] = {}
        for class_name in object_info.nodes.keys():
            canonical = get_canonical_name(class_name, self.alias_index)
            # Store mapping from canonical to actual class name
            self._available_canonical[canonical] = class_name
    
    def check_compatibility(self, manifest: WorkflowManifest) -> CompatibilityResult:
        """
        Check if a workflow manifest is compatible with this backend.
        
        Args:
            manifest: The workflow manifest to check
            
        Returns:
            CompatibilityResult with detailed compatibility information
        """
        missing_nodes: List[MissingNodeInfo] = []
        missing_models: List[MissingModelInfo] = []
        schema_mismatches: List[SchemaMismatchInfo] = []
        
        # Check required nodes
        for node_req in manifest.required_nodes:
            all_names = get_all_known_names_for(node_req.node_class, ALL_ALIASES)
            all_names.add(node_req.node_class)
            
            # Check if any variant of this node is available
            found = False
            found_class_name: Optional[str] = None
            for name in all_names:
                if name in self.object_info.nodes:
                    found = True
                    found_class_name = name
                    break
                # Also check canonical mapping
                canonical = get_canonical_name(name, self.alias_index)
                if canonical in self._available_canonical:
                    found = True
                    found_class_name = self._available_canonical[canonical]
                    break
            
            if not found:
                missing_nodes.append(MissingNodeInfo(
                    canonical_name=node_req.node_class,
                    required=node_req.required,
                    description=node_req.description,
                    aliases_checked=sorted(list(all_names)),
                ))
            elif node_req.required_inputs and found_class_name:
                # Check input schema compatibility
                node_spec = self.object_info.nodes[found_class_name]
                mismatches = self._check_input_schema(node_req, node_spec)
                schema_mismatches.extend(mismatches)
        
        # Check required models
        # Note: Model availability requires additional API calls or file system access
        # For now, we record the requirements but mark as "unknown" availability
        for model_req in manifest.required_models:
            # TODO: Implement actual model checking via /view with type=models
            # or by querying the file system if we have access
            missing_models.append(MissingModelInfo(
                logical_id=model_req.logical_id,
                model_type=model_req.model_type,
                required=model_req.required,
                description=model_req.description,
                alternatives=model_req.alternatives,
            ))
        
        # Determine overall status
        required_missing_nodes = [n for n in missing_nodes if n.required]
        required_missing_models = [m for m in missing_models if m.required]
        
        if required_missing_nodes:
            status = CompatibilityStatus.MISSING_NODES
            is_compatible = False
            message = f"Missing {len(required_missing_nodes)} required node(s)"
        elif required_missing_models:
            status = CompatibilityStatus.MISSING_MODELS
            is_compatible = False
            message = f"Missing {len(required_missing_models)} required model(s)"
        elif schema_mismatches:
            # Schema mismatches are warnings unless they're critical
            critical_mismatches = [s for s in schema_mismatches if s.severity == "error"]
            if critical_mismatches:
                status = CompatibilityStatus.SCHEMA_MISMATCH
                is_compatible = False
                message = f"Found {len(critical_mismatches)} critical schema mismatch(es)"
            else:
                status = CompatibilityStatus.COMPATIBLE
                is_compatible = True
                message = f"Compatible with {len(schema_mismatches)} minor schema warning(s)"
        else:
            status = CompatibilityStatus.COMPATIBLE
            is_compatible = True
            message = "Fully compatible"
        
        return CompatibilityResult(
            workflow_id=manifest.workflow_id,
            status=status,
            is_compatible=is_compatible,
            missing_nodes=missing_nodes,
            missing_models=missing_models,
            schema_mismatches=schema_mismatches,
            available_nodes=list(self.object_info.nodes.keys()),
            available_models={},  # TODO: Populate from model listing
            message=message,
        )
    
    def _check_input_schema(
        self, node_req: NodeRequirement, node_spec: NodeSpec
    ) -> List[SchemaMismatchInfo]:
        """
        Check if the node spec matches the required input schema.
        
        Args:
            node_req: The node requirement from the manifest
            node_spec: The actual node specification from the backend
            
        Returns:
            List of schema mismatches found
        """
        mismatches: List[SchemaMismatchInfo] = []
        
        # Build input name -> type map from spec
        spec_inputs: Dict[str, str] = {}
        for inp in node_spec.inputs:
            spec_inputs[inp.name] = inp.type if isinstance(inp.type, str) else inp.type.value
        
        # Check required inputs
        for input_name, expected_type in node_req.required_inputs.items():
            if input_name not in spec_inputs:
                mismatches.append(SchemaMismatchInfo(
                    node_class=node_req.node_class,
                    input_name=input_name,
                    expected_type=expected_type,
                    actual_type="missing",
                    severity="error",
                ))
            elif spec_inputs[input_name] != expected_type:
                # Type mismatch - could be warning or error depending on compatibility
                mismatches.append(SchemaMismatchInfo(
                    node_class=node_req.node_class,
                    input_name=input_name,
                    expected_type=expected_type,
                    actual_type=spec_inputs[input_name],
                    severity="warning",
                ))
        
        return mismatches
    
    def is_node_available(self, canonical_name: str) -> bool:
        """
        Check if a node (by canonical name) is available.
        
        Args:
            canonical_name: The canonical node name
            
        Returns:
            True if the node or any of its aliases is available
        """
        all_names = get_all_known_names_for(canonical_name, ALL_ALIASES)
        all_names.add(canonical_name)
        
        for name in all_names:
            if name in self.object_info.nodes:
                return True
            canonical = get_canonical_name(name, self.alias_index)
            if canonical in self._available_canonical:
                return True
        
        return False
    
    def get_available_node_names(self) -> Set[str]:
        """
        Get all available node class names.
        
        Returns:
            Set of available node class names
        """
        return set(self.object_info.nodes.keys())
    
    def get_node_spec(self, class_name: str) -> Optional[NodeSpec]:
        """
        Get the specification for a node by class name.
        
        Args:
            class_name: The node class name (or alias)
            
        Returns:
            NodeSpec if found, None otherwise
        """
        # Direct lookup
        if class_name in self.object_info.nodes:
            return self.object_info.nodes[class_name]
        
        # Canonical lookup
        canonical = get_canonical_name(class_name, self.alias_index)
        if canonical in self._available_canonical:
            actual_name = self._available_canonical[canonical]
            return self.object_info.nodes.get(actual_name)
        
        return None
