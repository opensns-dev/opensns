import asyncio
import httpx
from app.core.interfaces import BaseImageAdapter, AdCreative, GenerationResult
from app.core.config import settings


class BFLAdapter(BaseImageAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "BFL_API_KEY", None)
        self.base_url = "https://api.bfl.ai/v1/flux-pro-1.1"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("BFL_API_KEY is not configured")

        prompt = (
            creative.image_prompt
            or f"professional product photography for {creative.platform} advertisement, clean modern background, studio lighting, commercial quality"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "x-key": f"{self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"prompt": prompt, "width": 1792, "height": 1024},
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            polling_url = result.get("polling_url")
            if not polling_url:
                raise RuntimeError("No polling URL returned from BFL")

            final_result: dict = {}
            for _ in range(60):
                poll_response = await client.get(
                    polling_url,
                    headers={"x-key": f"{self.api_key}"},
                    timeout=120.0,
                )
                poll_response.raise_for_status()
                final_result = poll_response.json()

                if final_result.get("status") == "Ready":
                    break

                await asyncio.sleep(2)
            else:
                raise RuntimeError("BFL image generation timed out")

            output = final_result.get("result", {}).get("output")
            if isinstance(output, list):
                image_url = output[0] if output else None
            else:
                image_url = output

            if not image_url:
                raise RuntimeError("No image returned from BFL")

            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_data = image_response.content

            if not image_data:
                raise RuntimeError("No image returned from BFL")

            return GenerationResult(
                image_url=image_url,
                image_data=image_data,
                metadata={
                    "model": "flux-pro-1.1",
                    "prompt": prompt,
                    "width": 1792,
                    "height": 1024,
                    "status": final_result.get("status"),
                    "id": result.get("id"),
                },
            )
