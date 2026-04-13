import base64
import logging

from app.core.interfaces import BaseProductPhotoAdapter, GenerationResult
from app.core.config import settings
from app.core.http_client import http_client_manager

logger = logging.getLogger(__name__)


class FalProductPhotoAdapter(BaseProductPhotoAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.FAL_KEY
        self.base_url = "https://fal.run"

    async def remove_background(self, image_data: bytes) -> bytes:
        if not self.api_key:
            raise ValueError("FAL_KEY is not configured")

        image_b64 = base64.b64encode(image_data).decode("utf-8")
        image_url = f"data:image/png;base64,{image_b64}"

        client = await http_client_manager.get_client()
        try:
            response = await client.post(
                f"{self.base_url}/fal-ai/birefnet",
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "image_url": image_url,
                    "model": "General Use (Heavy)",
                    "operating_resolution": "1024x1024",
                    "output_format": "png",
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            output_url = result.get("image", {}).get("url")
            if not output_url:
                raise RuntimeError("No output image from background removal")

            img_response = await client.get(output_url, timeout=60.0)
            img_response.raise_for_status()
            return img_response.content
        except Exception as e:
            logger.error("Background removal failed: %s", str(e))
            raise

    async def generate_product_shot(
        self, product_image: bytes, scene_prompt: str, angle: str
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("FAL_KEY is not configured")

        image_b64 = base64.b64encode(product_image).decode("utf-8")
        image_url = f"data:image/png;base64,{image_b64}"

        angle_descriptions = {
            "FRONT": "front-facing view, eye level",
            "SIDE": "side angle, 45 degree perspective",
            "TOP_DOWN": "top-down flat lay, bird's eye view",
            "LIFESTYLE": "lifestyle setting, in-use context",
            "MODEL_HOLDING": "person holding the product, natural pose",
            "STUDIO": "studio lighting, clean white background, commercial quality",
        }
        angle_desc = angle_descriptions.get(angle, "professional product photography")

        prompt = (
            f"{scene_prompt}, {angle_desc}, "
            "professional product photography, high resolution, commercial quality"
        )

        client = await http_client_manager.get_client()
        try:
            response = await client.post(
                f"{self.base_url}/fal-ai/flux/schnell",
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "image_url": image_url,
                    "image_size": "square_hd",
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
                result_url = image_info.get("url")

                image_bytes = None
                if result_url:
                    img_response = await client.get(result_url, timeout=60.0)
                    img_response.raise_for_status()
                    image_bytes = img_response.content

                return GenerationResult(
                    image_url=result_url,
                    image_data=image_bytes,
                    metadata={
                        "model": "fal-ai/flux/schnell",
                        "angle": angle,
                        "prompt": prompt,
                        "width": image_info.get("width"),
                        "height": image_info.get("height"),
                    },
                )

            raise RuntimeError("No image returned from Fal.ai")
        except Exception as e:
            logger.error(
                "Product shot generation failed for angle %s: %s", angle, str(e)
            )
            raise
