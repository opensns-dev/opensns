import base64
import base64
import httpx

from app.core.config import settings
from app.core.interfaces import AdCreative, BaseImageAdapter, GenerationResult


class OpenRouterImageAdapter(BaseImageAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "openai/gpt-image-1",
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/images/generations"

    async def generate_ad_image(
        self, product_image: bytes, creative: AdCreative
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

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
                json={"model": self.model, "prompt": prompt, "n": 1, "size": "1792x1024"},
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            if "data" in result and len(result["data"]) > 0:
                image_info = result["data"][0]
                image_url = image_info.get("url")
                b64_json = image_info.get("b64_json")

                if image_url:
                    image_response = await client.get(image_url)
                    image_response.raise_for_status()
                    image_data = image_response.content
                elif b64_json:
                    image_data = base64.b64decode(b64_json)
                else:
                    image_data = None

                if image_url or image_data:
                    return GenerationResult(
                        image_url=image_url,
                        image_data=image_data,
                        metadata={
                            "model": self.model,
                            "prompt": prompt,
                            "provider": "openrouter",
                        },
                    )

            raise RuntimeError("No image returned from OpenRouter")
