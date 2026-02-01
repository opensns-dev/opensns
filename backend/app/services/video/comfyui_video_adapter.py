import httpx
import uuid
import asyncio
import time
from typing import Dict, Any
from app.services.video.interfaces import (
    BaseVideoAdapter,
    VideoGenerationRequest,
    VideoGenerationResult,
)


class ComfyUIVideoAdapter(BaseVideoAdapter):
    def __init__(
        self,
        base_url: str = "http://localhost:8188",
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    async def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow, "client_id": self.client_id},
            )
            response.raise_for_status()
            return response.json()["prompt_id"]

    async def _wait_for_completion(
        self, prompt_id: str, timeout: float = 300.0
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            start_time = time.monotonic()
            while True:
                if time.monotonic() - start_time > timeout:
                    raise TimeoutError(
                        f"ComfyUI video generation timed out after {timeout}s"
                    )

                response = await client.get(f"{self.base_url}/history/{prompt_id}")
                response.raise_for_status()
                history = response.json()

                if prompt_id in history:
                    return history[prompt_id]

                await asyncio.sleep(2.0)

    def _build_image_to_video_workflow(
        self,
        image_path: str,
        motion_prompt: str,
        frames: int = 49,
    ) -> Dict[str, Any]:
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": image_path},
            },
            "2": {
                "class_type": "CLIPVisionLoader",
                "inputs": {"clip_name": "clip_vision_vit_h.safetensors"},
            },
            "3": {
                "class_type": "CogVideoXImageEncode",
                "inputs": {
                    "image": ["1", 0],
                    "vae": ["5", 2],
                    "clip_vision": ["2", 0],
                },
            },
            "4": {
                "class_type": "CogVideoXTextEncode",
                "inputs": {
                    "prompt": motion_prompt,
                    "text_encoder": ["5", 1],
                },
            },
            "5": {
                "class_type": "CogVideoXModelLoader",
                "inputs": {"model_name": "cogvideox_5b_I2V.safetensors"},
            },
            "6": {
                "class_type": "CogVideoXSampler",
                "inputs": {
                    "model": ["5", 0],
                    "positive": ["4", 0],
                    "negative": ["4", 0],
                    "image_cond_latents": ["3", 0],
                    "num_frames": frames,
                    "steps": 50,
                    "cfg": 6.0,
                    "seed": -1,
                },
            },
            "7": {
                "class_type": "CogVideoXDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["5", 2],
                },
            },
            "8": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["7", 0],
                    "frame_rate": 8,
                    "filename_prefix": "opensns_video",
                    "format": "video/h264-mp4",
                },
            },
        }

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        if not request.images:
            raise ValueError("At least one image is required")

        workflow = self._build_image_to_video_workflow(
            image_path=request.images[0],
            motion_prompt=f"Smooth product showcase, professional advertisement, {request.aspect_ratio}",
            frames=int(request.duration * 8),
        )

        prompt_id = await self._queue_prompt(workflow)
        history = await self._wait_for_completion(prompt_id)

        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "gifs" in node_output:
                video_info = node_output["gifs"][0]
                return VideoGenerationResult(
                    video_url=f"{self.base_url}/view?filename={video_info['filename']}&type=output",
                    duration=request.duration,
                    metadata={
                        "prompt_id": prompt_id,
                        "filename": video_info["filename"],
                    },
                )

        raise RuntimeError("No video output found in ComfyUI response")

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        request = VideoGenerationRequest(
            images=[image_url],
            duration=duration,
        )
        return await self.generate_video(request)
