import httpx
import uuid
import asyncio
import base64
import time
from typing import Dict, Any

from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult
from app.services.comfyui_portability import (
    ComfyUIDiscovery,
    NodeAliasResolver,
    ModelRegistry,
    WorkflowLoader,
    MissingNodeError,
    MissingModelError,
    ComfyUICompatibilityError,
)


class ComfyUIAdapter(BaseImageAdapter):
    """ComfyUI image adapter with portability foundation.

    Builds workflows from manifests instead of hardcoded dicts,
    resolves node aliases and model mappings through the discovery layer,
    and provides clear compatibility errors.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8188",
        output_dir: str = "/output",
        model_mappings: Dict[str, str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.client_id = str(uuid.uuid4())

        # Initialize portability components
        self.discovery = ComfyUIDiscovery(base_url)
        self.alias_resolver = NodeAliasResolver(self.discovery)
        self.model_registry = ModelRegistry()
        self.workflow_loader = WorkflowLoader()

        # Register custom model mappings if provided
        if model_mappings:
            for logical_id, filename in model_mappings.items():
                self.model_registry.register_model(logical_id, "checkpoints", filename)

    async def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a workflow prompt with ComfyUI."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/prompt",
                    json={"prompt": workflow, "client_id": self.client_id},
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()["prompt_id"]
            except httpx.HTTPStatusError as e:
                raise ComfyUICompatibilityError(
                    f"ComfyUI API error: {e.response.status_code}",
                    {"detail": e.response.text},
                ) from e

    async def _wait_for_completion(
        self, prompt_id: str, timeout: float = 300.0
    ) -> Dict[str, Any]:
        """Wait for workflow completion with timeout."""
        async with httpx.AsyncClient() as client:
            start_time = time.monotonic()
            while True:
                if time.monotonic() - start_time > timeout:
                    raise TimeoutError(f"ComfyUI generation timed out after {timeout}s")

                try:
                    response = await client.get(
                        f"{self.base_url}/history/{prompt_id}",
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    history = response.json()

                    if prompt_id in history:
                        entry = history[prompt_id]
                        status = entry.get("status", {})
                        status_str = status.get("status_str", "")
                        if status_str in ("success", "error"):
                            return entry
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        pass  # Prompt not found yet, keep waiting
                    else:
                        raise

                await asyncio.sleep(1.0)

    async def _get_image(
        self, filename: str, subfolder: str = "", folder_type: str = "output"
    ) -> bytes:
        """Fetch generated image from ComfyUI."""
        async with httpx.AsyncClient() as client:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            response = await client.get(f"{self.base_url}/view", params=params)
            response.raise_for_status()
            return response.content

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        """Generate an ad image using ComfyUI with background replacement.

        Args:
            product_image: Raw product image bytes
            creative: Ad creative specification

        Returns:
            GenerationResult with generated image

        Raises:
            ComfyUICompatibilityError: If ComfyUI is missing required nodes or models
            TimeoutError: If generation times out
        """
        product_image_b64 = base64.b64encode(product_image).decode("utf-8")

        background_prompt = (
            creative.image_prompt
            or f"professional product photography, {creative.platform} advertisement, clean studio background, soft lighting"
        )

        await self.alias_resolver.resolve_with_discovery("load_image_base64")

        # Get the predefined manifest
        manifest = self.workflow_loader.get_preset("background_replacement")
        if not manifest:
            raise ComfyUICompatibilityError(
                "Background replacement workflow manifest not found"
            )

        # Build workflow with portability layer
        try:
            workflow = manifest.to_comfyui_workflow(
                node_resolver=self.alias_resolver,
                model_registry=self.model_registry,
                parameters={
                    "image_base64": product_image_b64,
                    "prompt": background_prompt,
                },
            )
        except MissingNodeError as e:
            raise ComfyUICompatibilityError(
                f"ComfyUI installation is missing required nodes for image generation. "
                f"Please install the required custom nodes: {e.message}",
                e.details,
            ) from e
        except MissingModelError as e:
            raise ComfyUICompatibilityError(
                f"ComfyUI is missing required models. Please download: {e.message}",
                e.details,
            ) from e

        # Queue and wait for completion
        prompt_id = await self._queue_prompt(workflow)
        history = await self._wait_for_completion(prompt_id)

        # Extract output from history
        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                image_info = node_output["images"][0]
                filename = image_info["filename"]
                subfolder = image_info.get("subfolder", "")
                folder_type = image_info.get("type", "output")

                image_data = await self._get_image(
                    filename=filename,
                    subfolder=subfolder,
                    folder_type=folder_type,
                )

                # Build a viewable URL for the generated image
                from urllib.parse import urlencode

                view_params = {"filename": filename, "type": folder_type}
                if subfolder:
                    view_params["subfolder"] = subfolder
                image_url = f"{self.base_url}/view?{urlencode(view_params)}"

                return GenerationResult(
                    image_url=image_url,
                    image_data=image_data,
                    metadata={
                        "prompt_id": prompt_id,
                        "filename": filename,
                        "workflow": "background_replacement",
                    },
                )

        raise ComfyUICompatibilityError(
            "No image output found in ComfyUI response",
            {"available_outputs": list(outputs.keys())},
        )

    async def generate_text_to_image(self, creative: AdCreative) -> GenerationResult:
        """Generate an ad image from text prompt only (no input image).

        Uses SDXL txt2img workflow for cases where no real product image
        is available (e.g., scraping failed).

        Args:
            creative: Ad creative specification with image_prompt

        Returns:
            GenerationResult with generated image

        Raises:
            ComfyUICompatibilityError: If ComfyUI is missing required nodes or models
            TimeoutError: If generation times out
        """
        image_prompt = (
            creative.image_prompt
            or f"professional product photography, {creative.platform} advertisement, "
            f"clean studio background, soft lighting, commercial quality, 4k"
        )

        await self.alias_resolver.resolve_with_discovery("checkpoint_loader")

        manifest = self.workflow_loader.get_preset("text_to_image")
        if not manifest:
            raise ComfyUICompatibilityError("Text-to-image workflow manifest not found")

        import random

        seed = random.randint(0, 2**32 - 1)

        try:
            workflow = manifest.to_comfyui_workflow(
                node_resolver=self.alias_resolver,
                model_registry=self.model_registry,
                parameters={
                    "prompt": image_prompt,
                    "seed": seed,
                },
            )
        except MissingNodeError as e:
            raise ComfyUICompatibilityError(
                f"ComfyUI installation is missing required nodes for text-to-image. "
                f"Please install the required custom nodes: {e.message}",
                e.details,
            ) from e
        except MissingModelError as e:
            raise ComfyUICompatibilityError(
                f"ComfyUI is missing required models for text-to-image. "
                f"Please download: {e.message}",
                e.details,
            ) from e

        prompt_id = await self._queue_prompt(workflow)
        history = await self._wait_for_completion(prompt_id)

        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                image_info = node_output["images"][0]
                filename = image_info["filename"]
                subfolder = image_info.get("subfolder", "")
                folder_type = image_info.get("type", "output")

                image_data = await self._get_image(
                    filename=filename,
                    subfolder=subfolder,
                    folder_type=folder_type,
                )

                from urllib.parse import urlencode

                view_params = {"filename": filename, "type": folder_type}
                if subfolder:
                    view_params["subfolder"] = subfolder
                image_url = f"{self.base_url}/view?{urlencode(view_params)}"

                return GenerationResult(
                    image_url=image_url,
                    image_data=image_data,
                    metadata={
                        "prompt_id": prompt_id,
                        "filename": filename,
                        "workflow": "text_to_image",
                        "seed": seed,
                    },
                )

        raise ComfyUICompatibilityError(
            "No image output found in ComfyUI text-to-image response",
            {"available_outputs": list(outputs.keys())},
        )
