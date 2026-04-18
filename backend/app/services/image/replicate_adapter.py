import base64
import asyncio

import httpx

from app.core.config import settings
from app.core.interfaces import AdCreative, BaseImageAdapter, GenerationResult


class ReplicateAdapter(BaseImageAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "black-forest-labs/flux-schnell",
    ):
        self.api_key = api_key or settings.REPLICATE_API_TOKEN
        self.model = model
        self.base_url = "https://api.replicate.com/v1/predictions"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("REPLICATE_API_TOKEN is not configured")

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
                    "model": self.model,
                    "input": {
                        "prompt": prompt,
                        "num_outputs": 1,
                        "aspect_ratio": "16:9",
                    },
                },
                timeout=120.0,
            )
            response.raise_for_status()
            prediction = response.json()
            prediction_url = prediction.get("urls", {}).get("get")

            if not prediction_url:
                raise RuntimeError("No image returned from Replicate")

            for _ in range(60):
                poll_response = await client.get(
                    prediction_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=120.0,
                )
                poll_response.raise_for_status()
                result = poll_response.json()
                status = result.get("status")

                if status == "succeeded":
                    output = result.get("output") or []
                    if output:
                        image_url = output[0]
                        image_response = await client.get(image_url)
                        image_response.raise_for_status()
                        return GenerationResult(
                            image_url=image_url,
                            image_data=image_response.content,
                            metadata={
                                "model": self.model,
                                "prompt": prompt,
                                "prediction_id": result.get("id"),
                                "provider": "replicate",
                            },
                        )
                    break

                if status in {"failed", "canceled", "cancelled"}:
                    raise RuntimeError(f"Replicate prediction {status}")

                await asyncio.sleep(2)

            raise RuntimeError("No image returned from Replicate")
