"""Google Imagen 4 image generation adapter."""

import base64
import logging

import httpx

from app.core.exceptions import APIKeyNotConfiguredError
from app.core.interfaces import AdCreative, BaseImageAdapter, GenerationResult

logger = logging.getLogger(__name__)


class GeminiImageAdapter(BaseImageAdapter):
    """Image generation via Google Imagen 4 (predict endpoint)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "imagen-4.0-generate-001",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Imagen")

        if product_image:
            logger.info("GeminiImageAdapter: product_image ignored (prompt-only generation via Imagen 4)")

        prompt = (
            creative.image_prompt
            or (
                f"professional product photography for {creative.platform} "
                "advertisement, clean modern background, studio lighting, "
                "commercial quality"
            )
        )

        url = f"{self.base_url}/models/{self.model}:predict"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "personGeneration": "dont_allow",
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        predictions = data.get("predictions", [])
        if not predictions:
            raise RuntimeError("No image returned from Imagen 4")

        prediction = predictions[0]
        image_b64 = prediction.get("bytesBase64Encoded", "")
        mime_type = prediction.get("mimeType", "image/png")

        if not image_b64:
            raise RuntimeError("No image data in Imagen 4 response")

        image_data = base64.b64decode(image_b64)

        return GenerationResult(
            image_data=image_data,
            metadata={
                "engine": "gemini-image",
                "model": self.model,
                "prompt": prompt,
                "mime_type": mime_type,
            },
        )
