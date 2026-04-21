"""Google Veo video generation adapter."""

import asyncio
import base64
import logging

import httpx

from app.core.exceptions import APIKeyNotConfiguredError
from app.services.video.interfaces import (
    BaseVideoAdapter,
    VideoGenerationRequest,
    VideoGenerationResult,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 10
MAX_POLL_SECONDS = 600


class GeminiVideoAdapter(BaseVideoAdapter):
    """Video generation via Google Veo (predictLongRunning endpoint)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "veo-3.1-generate-preview",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Veo")

        prompt = (
            request.prompt
            or (
                f"Smooth camera movement, professional product advertisement, "
                f"{request.aspect_ratio} format"
            )
        )

        payload: dict = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "aspectRatio": request.aspect_ratio,
            },
        }

        if request.images:
            image_data = await self._download_image(request.images[0])
            if image_data:
                payload["instances"][0]["image"] = {
                    "bytesBase64Encoded": image_data,
                }
            else:
                logger.info("Image download failed, proceeding with text-only video generation")

        return await self._run_generation(payload)

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Veo")

        image_data = await self._download_image(image_url)
        if not image_data:
            raise RuntimeError(f"Failed to download source image for Veo: {image_url}")

        payload: dict = {
            "instances": [
                {
                    "prompt": motion_prompt,
                    "image": {"bytesBase64Encoded": image_data},
                }
            ],
            "parameters": {
                "aspectRatio": "9:16",
            },
        }

        return await self._run_generation(payload)

    async def _run_generation(self, payload: dict) -> VideoGenerationResult:
        api_key = self.api_key
        if not api_key:
            raise APIKeyNotConfiguredError("Google Veo")

        url = f"{self.base_url}/models/{self.model}:predictLongRunning"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                params={"key": api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            operation = response.json()

        operation_name = operation.get("name")
        if not operation_name:
            raise RuntimeError("No operation name returned from Veo")

        return await self._poll_operation(operation_name, api_key)

    async def _poll_operation(
        self, operation_name: str, api_key: str
    ) -> VideoGenerationResult:
        poll_url = f"{self.base_url}/{operation_name}"
        elapsed = 0

        async with httpx.AsyncClient(timeout=60.0) as client:
            while elapsed < MAX_POLL_SECONDS:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                elapsed += POLL_INTERVAL_SECONDS

                response = await client.get(
                    poll_url,
                    params={"key": api_key},
                )
                response.raise_for_status()
                status = response.json()

                if status.get("done"):
                    return self._parse_completed(status)

        raise TimeoutError(
            f"Veo video generation timed out after {MAX_POLL_SECONDS}s"
        )

    def _parse_completed(self, status: dict) -> VideoGenerationResult:
        error = status.get("error")
        if error:
            code = error.get("code", "UNKNOWN")
            message = error.get("message", "Unknown error")
            raise RuntimeError(f"Veo generation failed ({code}): {message}")

        gen_response = (
            status.get("response", {}).get("generateVideoResponse", {})
        )
        samples = gen_response.get("generatedSamples", [])

        if not samples:
            raise RuntimeError("Veo returned no video samples")

        video_uri = samples[0].get("video", {}).get("uri")
        if not video_uri:
            raise RuntimeError("Veo returned sample without video URI")

        return VideoGenerationResult(
            video_url=video_uri,
            metadata={
                "engine": "gemini-video",
                "model": self.model,
            },
        )

    async def _download_image(self, url: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return base64.b64encode(response.content).decode("utf-8")
        except httpx.HTTPError:
            logger.warning("Failed to download image for Veo: %s", url)
            return None
