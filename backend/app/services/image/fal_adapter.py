import httpx
import base64
from typing import Dict, Any
from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult
from app.core.config import settings


class FalAIAdapter(BaseImageAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "fal-ai/flux/schnell",
    ):
        self.api_key = api_key or settings.FAL_KEY
        self.model = model
        self.base_url = "https://fal.run"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("FAL_KEY is not configured")

        product_image_b64 = base64.b64encode(product_image).decode("utf-8")
        image_url = f"data:image/png;base64,{product_image_b64}"

        prompt = (
            creative.image_prompt
            or f"professional product photography for {creative.platform} advertisement, clean modern background, studio lighting, commercial quality"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.model}",
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "image_url": image_url,
                    "image_size": "landscape_16_9",
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                    "num_images": 1,
                    "enable_safety_checker": True,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            if "images" in result and len(result["images"]) > 0:
                image_info = result["images"][0]
                image_url = image_info.get("url")

                if image_url:
                    image_response = await client.get(image_url)
                    image_response.raise_for_status()
                    image_data = image_response.content
                else:
                    image_data = None

                return GenerationResult(
                    image_url=image_url,
                    image_data=image_data,
                    metadata={
                        "model": self.model,
                        "prompt": prompt,
                        "width": image_info.get("width"),
                        "height": image_info.get("height"),
                    },
                )

            raise RuntimeError("No image returned from Fal.ai")


class FluxProAdapter(FalAIAdapter):
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key, model="fal-ai/flux-pro")


class FluxDevAdapter(FalAIAdapter):
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key, model="fal-ai/flux/dev")
