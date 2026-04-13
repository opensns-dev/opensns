"""
ComfyUI discovery client for querying backend capabilities.

Provides methods to fetch and parse:
- /object_info: Available nodes and their schemas
- /system_stats: System information and device capabilities
"""

from typing import Any, Dict, Optional
import httpx
from app.services.comfyui.types import (
    NodeSpec,
    NodeInputSpec,
    NodeOutputSpec,
    InputType,
    ObjectInfoResponse,
    SystemStatsResponse,
)


class ComfyUIDiscoveryClient:
    """
    Client for discovering ComfyUI backend capabilities.

    This client queries the ComfyUI REST API to understand:
    - What nodes are available
    - What models are installed
    - System capabilities

    Example:
        client = ComfyUIDiscoveryClient("http://localhost:8188")
        info = await client.get_object_info()
        stats = await client.get_system_stats()
    """

    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url.rstrip("/")

    async def get_object_info(self) -> ObjectInfoResponse:
        """
        Fetch and parse the /object_info endpoint.

        Returns:
            ObjectInfoResponse containing all available node types

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/object_info")
            response.raise_for_status()
            raw_data = response.json()

        nodes: Dict[str, NodeSpec] = {}
        for class_name, node_data in raw_data.items():
            try:
                node_spec = self._parse_node_spec(class_name, node_data)
                nodes[class_name] = node_spec
            except Exception as e:
                # Log parsing errors but continue processing other nodes
                # This handles edge cases where custom nodes have unusual schemas
                print(f"Warning: Failed to parse node {class_name}: {e}")
                continue

        return ObjectInfoResponse(nodes=nodes, raw_response=raw_data)

    async def get_system_stats(self) -> SystemStatsResponse:
        """
        Fetch and parse the /system_stats endpoint.

        Returns:
            SystemStatsResponse containing system information

        Raises:
            httpx.HTTPError: If the request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/system_stats")
            response.raise_for_status()
            raw_data = response.json()

        return SystemStatsResponse(
            comfyui_version=raw_data.get("system", {}).get("comfyui_version"),
            python_version=raw_data.get("system", {}).get("python_version"),
            devices=raw_data.get("devices", []),
            memory=raw_data.get("memory", {}),
            raw_response=raw_data,
        )

    def _parse_node_spec(self, class_name: str, node_data: Dict[str, Any]) -> NodeSpec:
        """
        Parse a single node specification from /object_info response.

        Args:
            class_name: The node class type name
            node_data: Raw node data from ComfyUI

        Returns:
            Parsed NodeSpec
        """
        # Extract basic info
        display_name = node_data.get("display_name")
        category = node_data.get("category", "")
        description = node_data.get("description", "")

        # Parse input specifications
        inputs: list[NodeInputSpec] = []
        input_data = node_data.get("input", {})

        # Required inputs
        required_inputs = input_data.get("required", {})
        for name, spec in required_inputs.items():
            input_spec = self._parse_input_spec(name, spec, required=True)
            inputs.append(input_spec)

        # Optional inputs
        optional_inputs = input_data.get("optional", {})
        for name, spec in optional_inputs.items():
            input_spec = self._parse_input_spec(name, spec, required=False)
            inputs.append(input_spec)

        # Hidden inputs (like 'prompt', 'extra_pnginfo', 'unique_id')
        hidden_inputs = input_data.get("hidden", {})
        for name, spec in hidden_inputs.items():
            input_spec = self._parse_input_spec(name, spec, required=False)
            inputs.append(input_spec)

        # Parse output specifications
        outputs: list[NodeOutputSpec] = []
        output_types = node_data.get("output", [])
        output_names = node_data.get("output_name", [])
        output_is_list = node_data.get("output_is_list", [])

        for i, output_type in enumerate(output_types):
            output_name = output_names[i] if i < len(output_names) else f"output_{i}"
            outputs.append(
                NodeOutputSpec(
                    name=output_name,
                    type=output_type,
                    is_primary=(i == 0),  # First output is typically primary
                )
            )

        return NodeSpec(
            class_name=class_name,
            category=category,
            display_name=display_name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            output_is_list=output_is_list if output_is_list else [False] * len(outputs),
            output_name=output_names if output_names else None,
        )

    def _parse_input_spec(
        self, name: str, spec: Any, required: bool = True
    ) -> NodeInputSpec:
        """
        Parse a single input specification.

        ComfyUI input specs can be:
        - ["TYPE", config_dict] for primitive types with config
        - ["TYPE"] for primitive types without config
        - [["option1", "option2"], config] for COMBO types
        - Just "TYPE" string for simple types
        """
        # Handle string-only specs (simple type)
        if isinstance(spec, str):
            return NodeInputSpec(name=name, type=spec, required=required)

        # Handle list specs
        if isinstance(spec, list) and len(spec) > 0:
            first_elem = spec[0]
            config = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}

            # Check if it's a COMBO type (list of options as first element)
            if isinstance(first_elem, list):
                return NodeInputSpec(
                    name=name,
                    type=InputType.COMBO,
                    required=required,
                    default=config.get("default"),
                    options=first_elem,
                    min_value=config.get("min"),
                    max_value=config.get("max"),
                )
            else:
                # Primitive type with config
                type_str = first_elem
                return NodeInputSpec(
                    name=name,
                    type=type_str,
                    required=required,
                    default=config.get("default"),
                    min_value=config.get("min"),
                    max_value=config.get("max"),
                )

        # Fallback for unexpected formats
        return NodeInputSpec(name=name, type=str(spec), required=required)

    async def check_connection(self) -> bool:
        """
        Check if the ComfyUI server is reachable.

        Returns:
            True if the server responds, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/system_stats", timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False
