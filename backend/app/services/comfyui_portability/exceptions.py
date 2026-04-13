"""Exceptions for ComfyUI portability layer."""

from typing import List, Dict, Any, Optional


class ComfyUICompatibilityError(Exception):
    """Base exception for ComfyUI compatibility issues."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class MissingNodeError(ComfyUICompatibilityError):
    """Raised when a required node type is not available in ComfyUI."""

    def __init__(
        self,
        logical_node: str,
        attempted_aliases: List[str],
        available_nodes: Optional[List[str]] = None,
    ):
        message = (
            f"Missing required node '{logical_node}'. "
            f"Attempted aliases: {attempted_aliases}"
        )
        if available_nodes:
            message += (
                f". Available nodes: {available_nodes[:20]}..."
                if len(available_nodes) > 20
                else f". Available nodes: {available_nodes}"
            )
        super().__init__(
            message,
            details={
                "logical_node": logical_node,
                "attempted_aliases": attempted_aliases,
                "available_nodes": available_nodes,
            },
        )
        self.logical_node = logical_node
        self.attempted_aliases = attempted_aliases


class MissingModelError(ComfyUICompatibilityError):
    """Raised when a required model mapping cannot be resolved."""

    def __init__(
        self,
        logical_model: str,
        model_type: str,
        available_models: Optional[List[str]] = None,
    ):
        message = f"Missing model mapping for '{logical_model}' (type: {model_type})"
        if available_models:
            message += (
                f". Available models: {available_models[:20]}..."
                if len(available_models) > 20
                else f". Available models: {available_models}"
            )
        super().__init__(
            message,
            details={
                "logical_model": logical_model,
                "model_type": model_type,
                "available_models": available_models,
            },
        )
        self.logical_model = logical_model
        self.model_type = model_type


class UnsupportedOutputError(ComfyUICompatibilityError):
    """Raised when workflow output shape is not supported."""

    def __init__(
        self,
        output_key: str,
        expected_type: str,
        actual_outputs: Optional[List[str]] = None,
    ):
        message = f"Unsupported output shape: expected '{output_key}' of type '{expected_type}'"
        if actual_outputs:
            message += f". Actual outputs: {actual_outputs}"
        super().__init__(
            message,
            details={
                "output_key": output_key,
                "expected_type": expected_type,
                "actual_outputs": actual_outputs,
            },
        )
        self.output_key = output_key
        self.expected_type = expected_type


class WorkflowValidationError(ComfyUICompatibilityError):
    """Raised when workflow manifest fails validation."""

    def __init__(self, errors: List[str]):
        message = f"Workflow validation failed: {'; '.join(errors)}"
        super().__init__(message, details={"errors": errors})
        self.errors = errors
