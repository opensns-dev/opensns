import httpx
import json
import uuid
import asyncio
import base64
import time
from typing import Dict, Any
from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult


class ComfyUIAdapter(BaseImageAdapter):
    def __init__(
        self,
        base_url: str = "http://localhost:8188",
        output_dir: str = "/output",
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
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
        self, prompt_id: str, timeout: float = 120.0
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            start_time = time.monotonic()
            while True:
                if time.monotonic() - start_time > timeout:
                    raise TimeoutError(f"ComfyUI generation timed out after {timeout}s")

                response = await client.get(f"{self.base_url}/history/{prompt_id}")
                response.raise_for_status()
                history = response.json()

                if prompt_id in history:
                    return history[prompt_id]

                await asyncio.sleep(1.0)

    async def _get_image(
        self, filename: str, subfolder: str = "", folder_type: str = "output"
    ) -> bytes:
        async with httpx.AsyncClient() as client:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            response = await client.get(f"{self.base_url}/view", params=params)
            response.raise_for_status()
            return response.content

    def _build_background_replacement_workflow(
        self,
        product_image_base64: str,
        prompt: str,
        negative_prompt: str = "blurry, low quality, distorted",
    ) -> Dict[str, Any]:
        return {
            "1": {
                "class_type": "LoadImageBase64",
                "inputs": {"image": product_image_base64},
            },
            "2": {
                "class_type": "SAMModelLoader",
                "inputs": {"model_name": "sam_vit_h_4b8939.pth"},
            },
            "3": {
                "class_type": "GroundingDinoSAMSegment",
                "inputs": {
                    "image": ["1", 0],
                    "sam_model": ["2", 0],
                    "prompt": "product, main object",
                    "threshold": 0.3,
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "InpaintModelConditioning",
                "inputs": {
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "vae": ["4", 2],
                    "pixels": ["1", 0],
                    "mask": ["3", 1],
                },
            },
            "8": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["4", 0],
                    "positive": ["7", 0],
                    "negative": ["7", 1],
                    "latent_image": ["7", 2],
                    "seed": -1,
                    "steps": 30,
                    "cfg": 7.5,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 0.85,
                },
            },
            "9": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["8", 0], "vae": ["4", 2]},
            },
            "10": {
                "class_type": "ImageCompositeMasked",
                "inputs": {
                    "destination": ["9", 0],
                    "source": ["1", 0],
                    "mask": ["3", 1],
                    "x": 0,
                    "y": 0,
                },
            },
            "11": {
                "class_type": "SaveImage",
                "inputs": {"images": ["10", 0], "filename_prefix": "opensns_ad"},
            },
        }

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        product_image_b64 = base64.b64encode(product_image).decode("utf-8")

        background_prompt = (
            creative.image_prompt
            or f"professional product photography, {creative.platform} advertisement, clean studio background, soft lighting"
        )

        workflow = self._build_background_replacement_workflow(
            product_image_base64=product_image_b64,
            prompt=background_prompt,
        )

        prompt_id = await self._queue_prompt(workflow)
        history = await self._wait_for_completion(prompt_id)

        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                image_info = node_output["images"][0]
                image_data = await self._get_image(
                    filename=image_info["filename"],
                    subfolder=image_info.get("subfolder", ""),
                    folder_type=image_info.get("type", "output"),
                )
                return GenerationResult(
                    image_data=image_data,
                    metadata={
                        "prompt_id": prompt_id,
                        "filename": image_info["filename"],
                        "workflow": "background_replacement",
                    },
                )

        raise RuntimeError("No image output found in ComfyUI response")
