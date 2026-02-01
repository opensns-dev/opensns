import httpx
from app.services.video.interfaces import (
    BaseVideoAdapter,
    VideoGenerationRequest,
    VideoGenerationResult,
)
from app.core.config import settings


class FalVideoAdapter(BaseVideoAdapter):
    def __init__(
        self,
        api_key: str | None = None,
    ):
        self.api_key = api_key or settings.FAL_KEY
        self.base_url = "https://fal.run"

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        if not self.api_key:
            raise ValueError("FAL_KEY is not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/fal-ai/runway-gen3/turbo/image-to-video",
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "image_url": request.images[0] if request.images else "",
                    "prompt": f"Smooth camera movement, professional product advertisement, {request.aspect_ratio} format",
                    "duration": min(request.duration, 10),
                },
                timeout=180.0,
            )
            response.raise_for_status()
            result = response.json()

            video_url = result.get("video", {}).get("url")

            return VideoGenerationResult(
                video_url=video_url,
                duration=request.duration,
                metadata={
                    "model": "runway-gen3-turbo",
                    "request": request.model_dump(),
                },
            )

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        if not self.api_key:
            raise ValueError("FAL_KEY is not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/fal-ai/kling-video/v1/standard/image-to-video",
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "image_url": image_url,
                    "prompt": motion_prompt,
                    "duration": str(min(duration, 10)),
                    "aspect_ratio": "9:16",
                },
                timeout=180.0,
            )
            response.raise_for_status()
            result = response.json()

            video_url = result.get("video", {}).get("url")

            return VideoGenerationResult(
                video_url=video_url,
                duration=duration,
                metadata={"model": "kling-v1", "prompt": motion_prompt},
            )


class RunwayAdapter(BaseVideoAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.FAL_KEY
        self.base_url = "https://fal.run"

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        return await FalVideoAdapter(self.api_key).generate_video(request)

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/fal-ai/runway-gen3/turbo/image-to-video",
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "image_url": image_url,
                    "prompt": motion_prompt,
                    "duration": min(duration, 10),
                },
                timeout=180.0,
            )
            response.raise_for_status()
            result = response.json()

            return VideoGenerationResult(
                video_url=result.get("video", {}).get("url"),
                duration=duration,
                metadata={"model": "runway-gen3-turbo"},
            )
