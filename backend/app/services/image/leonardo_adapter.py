import asyncio
import httpx
from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult
from app.core.config import settings


class LeonardoAdapter(BaseImageAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "LEONARDO_API_KEY", None)
        self.base_url = "https://cloud.leonardo.ai/api/rest/v1/generations"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("LEONARDO_API_KEY is not configured")

        prompt = (
            creative.image_prompt
            or f"professional product photography for {creative.platform} advertisement, clean modern background, studio lighting, commercial quality"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "width": 1792,
                    "height": 1024,
                    "num_images": 1,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            generation_id = result.get("sdGenerationJob", {}).get("generationId")
            if not generation_id:
                raise RuntimeError("No generation ID returned from Leonardo")

            final_result: dict = {}
            for _ in range(40):
                poll_response = await client.get(
                    f"{self.base_url}/{generation_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=120.0,
                )
                poll_response.raise_for_status()
                final_result = poll_response.json()

                generated_images = final_result.get("generations_by_pk", {}).get(
                    "generated_images", []
                )
                if generated_images:
                    break

                await asyncio.sleep(3)
            else:
                raise RuntimeError("Leonardo image generation timed out")

            generated_images = final_result.get("generations_by_pk", {}).get("generated_images", [])
            if not generated_images:
                raise RuntimeError("No image returned from Leonardo")

            image_url = generated_images[0].get("url")
            if not image_url:
                raise RuntimeError("No image returned from Leonardo")

            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_data = image_response.content

            if not image_data:
                raise RuntimeError("No image returned from Leonardo")

            return GenerationResult(
                image_url=image_url,
                image_data=image_data,
                metadata={
                    "model": "leonardo",
                    "prompt": prompt,
                    "width": 1792,
                    "height": 1024,
                    "num_images": 1,
                    "generation_id": generation_id,
                },
            )
