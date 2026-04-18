import httpx
from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult
from app.core.config import settings


class StabilityAdapter(BaseImageAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "STABILITY_API_KEY", None)
        self.base_url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY is not configured")

        prompt = (
            creative.image_prompt
            or f"professional product photography for {creative.platform} advertisement, clean modern background, studio lighting, commercial quality"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "image/*",
                },
                files={
                    "prompt": (None, prompt),
                    "output_format": (None, "png"),
                    "aspect_ratio": (None, "16:9"),
                },
                timeout=120.0,
            )
            response.raise_for_status()
            image_data = response.content

            if not image_data:
                raise RuntimeError("No image returned from Stability.ai")

            return GenerationResult(
                image_url=None,
                image_data=image_data,
                metadata={
                    "model": "sd3",
                    "prompt": prompt,
                    "aspect_ratio": "16:9",
                    "output_format": "png",
                },
            )
