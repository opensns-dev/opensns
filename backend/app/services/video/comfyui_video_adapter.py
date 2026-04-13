import httpx
import uuid
import asyncio
import time
import logging
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs

from app.services.video.interfaces import (
    BaseVideoAdapter,
    VideoGenerationRequest,
    VideoGenerationResult,
)
from app.services.comfyui_portability import (
    ComfyUIDiscovery,
    NodeAliasResolver,
    ModelRegistry,
    WorkflowLoader,
    MissingNodeError,
    MissingModelError,
    ComfyUICompatibilityError,
)

logger = logging.getLogger(__name__)


class ComfyUIVideoAdapter(BaseVideoAdapter):
    """ComfyUI video adapter using AnimateDiff v3 for video generation.

    Builds workflows from manifests instead of hardcoded dicts,
    resolves node aliases and model mappings through the discovery layer,
    and provides clear compatibility errors.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8188",
        model_mappings: Dict[str, str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

        self.discovery = ComfyUIDiscovery(base_url)
        self.alias_resolver = NodeAliasResolver(self.discovery)
        self.model_registry = ModelRegistry()
        self.workflow_loader = WorkflowLoader()

        self.model_registry.register_model(
            "sd15_base", "checkpoints", "v1-5-pruned-emaonly.safetensors"
        )

        if model_mappings:
            for logical_id, filename in model_mappings.items():
                target_type = "vae" if "vae" in logical_id else "diffusion_models"
                self.model_registry.register_model(logical_id, target_type, filename)

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
        self, prompt_id: str, timeout: float = 600.0
    ) -> Dict[str, Any]:
        """Wait for workflow completion with timeout."""
        async with httpx.AsyncClient() as client:
            start_time = time.monotonic()
            while True:
                if time.monotonic() - start_time > timeout:
                    raise TimeoutError(
                        f"ComfyUI video generation timed out after {timeout}s"
                    )

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

                await asyncio.sleep(2.0)

    async def _resolve_image_for_comfyui(self, image_ref: str) -> str:
        """Resolve an image reference to a ComfyUI input filename.

        Handles ComfyUI /view URLs, HTTP URLs, and plain filenames.
        Downloads and uploads to ComfyUI input folder when needed.
        """
        if not image_ref.startswith("http"):
            return image_ref

        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(image_ref, timeout=30.0)
            resp.raise_for_status()
            image_bytes = resp.content

        parsed = urlparse(image_ref)
        qs = parse_qs(parsed.query)
        if "filename" in qs:
            filename = qs["filename"][0]
        else:
            filename = f"opensns_video_input_{uuid.uuid4().hex[:8]}.png"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/upload/image",
                files={"image": (filename, image_bytes, "image/png")},
                data={"overwrite": "true"},
                timeout=30.0,
            )
            resp.raise_for_status()
            result = resp.json()
            uploaded_name = result.get("name", filename)
            logger.info(f"Uploaded image to ComfyUI input: {uploaded_name}")
            return uploaded_name

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        if not request.images:
            raise ValueError("At least one image is required")

        image_filename = await self._resolve_image_for_comfyui(request.images[0])

        frame_rate = 8
        num_frames = min(int(request.duration * frame_rate), 16)

        motion_prompt = (
            request.prompt
            or f"Smooth product showcase, professional advertisement, {request.aspect_ratio}"
        )

        await self.alias_resolver.resolve_with_discovery("checkpoint_loader")

        manifest = self.workflow_loader.get_preset("animatediff_v3")
        if not manifest:
            raise ComfyUICompatibilityError(
                "AnimateDiff v3 workflow manifest not found"
            )

        try:
            workflow = manifest.to_comfyui_workflow(
                node_resolver=self.alias_resolver,
                model_registry=self.model_registry,
                parameters={
                    "image": image_filename,
                    "prompt": motion_prompt,
                    "batch_size": num_frames,
                    "frame_rate": frame_rate,
                },
            )
        except MissingNodeError as e:
            raise ComfyUICompatibilityError(
                f"ComfyUI is missing required nodes for video generation. "
                f"Please install AnimateDiff-Evolved and VHS custom nodes: {e.message}",
                e.details,
            ) from e
        except MissingModelError as e:
            raise ComfyUICompatibilityError(
                f"ComfyUI is missing required models for video generation. "
                f"Please download SD1.5 checkpoint and AnimateDiff v3 model: {e.message}",
                e.details,
            ) from e

        # Queue and wait for completion
        prompt_id = await self._queue_prompt(workflow)
        history = await self._wait_for_completion(prompt_id)

        status_info = history.get("status", {})
        if status_info.get("status_str") == "error":
            messages = status_info.get("messages", [])
            error_msgs = [
                str(m) for m in messages if isinstance(m, (list, tuple)) and len(m) > 1
            ]
            raise ComfyUICompatibilityError(
                f"ComfyUI workflow execution failed: {'; '.join(error_msgs) or 'unknown error'}",
                {"status": status_info},
            )

        outputs = history.get("outputs", {})

        # VHS_VideoCombine outputs under "gifs" key (not "videos" — counterintuitive naming).
        # Some versions may also use "videos" or "filenames" via RETURN_TYPES.
        for node_id, node_output in outputs.items():
            for output_key in ["gifs", "videos", "video"]:
                if output_key in node_output and node_output[output_key]:
                    video_info = node_output[output_key][0]
                    filename = video_info.get("filename", "")
                    subfolder = video_info.get("subfolder", "")
                    file_type = video_info.get("type", "output")

                    view_params = f"filename={filename}&type={file_type}"
                    if subfolder:
                        view_params += f"&subfolder={subfolder}"

                    return VideoGenerationResult(
                        video_url=f"{self.base_url}/view?{view_params}",
                        duration=request.duration,
                        metadata={
                            "prompt_id": prompt_id,
                            "filename": filename,
                            "output_key": output_key,
                        },
                    )

            if "filenames" in node_output and node_output["filenames"]:
                filenames = node_output["filenames"]
                first = filenames[0] if isinstance(filenames, list) else filenames
                if isinstance(first, dict):
                    filename = first.get("filename", "")
                else:
                    filename = str(first)

                if filename:
                    return VideoGenerationResult(
                        video_url=f"{self.base_url}/view?filename={filename}&type=output",
                        duration=request.duration,
                        metadata={
                            "prompt_id": prompt_id,
                            "filename": filename,
                            "output_key": "filenames",
                        },
                    )

        available_info = {}
        for node_id, node_output in outputs.items():
            available_info[node_id] = list(node_output.keys())

        raise ComfyUICompatibilityError(
            "No video output found in ComfyUI response",
            {"available_outputs": available_info, "status": status_info},
        )

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        request = VideoGenerationRequest(
            images=[image_url],
            duration=duration,
            prompt=motion_prompt,
        )
        return await self.generate_video(request)
