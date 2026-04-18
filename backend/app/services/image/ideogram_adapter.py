import httpx
from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult
from app.core.config import settings


class IdeogramAdapter(BaseImageAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "IDEOGRAM_API_KEY", None)
        self.base_url = "https://api.ideogram.ai/generate"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("IDEOGRAM_API_KEY is not configured")

        prompt = (
            creative.image_prompt
            or f"professional product photography for {creative.platform} advertisement, clean modern background, studio lighting, commercial quality"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Api-Key": f"{self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "image_request": {
                        "prompt": prompt,
                        "model": "V_2",
                        "aspect_ratio": "ASPECT_16_9",
                        "magic_prompt_option": "AUTO",
                    }
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            image_url = (result.get("data") or [{}])[0].get("url")
            if not image_url:
                raise RuntimeError("No image returned from Ideogram")

            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_data = image_response.content

            if not image_data:
                raise RuntimeError("No image returned from Ideogram")

            return GenerationResult(
                image_url=image_url,
                image_data=image_data,
                metadata={
                    "model": "V_2",
                    "prompt": prompt,
                    "aspect_ratio": "ASPECT_16_9",
                },
            )
