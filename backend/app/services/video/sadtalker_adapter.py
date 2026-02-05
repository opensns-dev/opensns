import asyncio
import logging
from typing import List

import httpx

from app.core.config import settings
from app.services.video.interfaces import (
    AvatarInfo,
    BaseVideoAdapter,
    UGCVideoRequest,
    VideoGenerationRequest,
    VideoGenerationResult,
    VoiceInfo,
)

logger = logging.getLogger(__name__)


class SadTalkerAdapter(BaseVideoAdapter):
    def __init__(self, endpoint_url: str | None = None):
        self.endpoint_url = endpoint_url or settings.SADTALKER_URL
        self.poll_interval = 3.0
        self.max_poll_attempts = 200

    def supports_ugc(self) -> bool:
        return True

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        raise NotImplementedError(
            "SadTalker specializes in UGC video generation. Use generate_ugc_video() instead."
        )

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        raise NotImplementedError(
            "SadTalker specializes in UGC video generation. Use generate_ugc_video() instead."
        )

    async def generate_ugc_video(
        self, request: UGCVideoRequest
    ) -> VideoGenerationResult:
        if not self.endpoint_url:
            raise ValueError("SADTALKER_URL is not configured")

        source_image = request.background_image_url
        if not source_image:
            raise ValueError("SadTalker requires a source image (background_image_url)")

        generate_payload = {
            "source_image_url": source_image,
            "text": request.script,
            "language": request.language,
            "voice_id": request.voice_id,
            "preprocess": "crop",
            "still_mode": False,
            "enhancer": "gfpgan",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.endpoint_url}/api/generate",
                json=generate_payload,
            )
            response.raise_for_status()
            result = response.json()

        task_id = result.get("task_id")
        if not task_id:
            raise ValueError(f"Failed to create task: {result}")

        video_url, duration = await self._poll_task_status(task_id)

        return VideoGenerationResult(
            video_url=video_url,
            duration=duration,
            metadata={
                "engine": "sadtalker",
                "task_id": task_id,
                "source_image": source_image,
                "script": request.script[:100],
            },
        )

    async def _poll_task_status(self, task_id: str) -> tuple[str, float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            consecutive_errors = 0
            for _ in range(self.max_poll_attempts):
                try:
                    response = await client.get(
                        f"{self.endpoint_url}/api/status/{task_id}",
                    )
                    response.raise_for_status()
                    result = response.json()
                    consecutive_errors = 0

                    status = result.get("status")

                    if status == "completed":
                        video_url = result.get("video_url")
                        if video_url and not video_url.startswith("http"):
                            video_url = f"{self.endpoint_url}{video_url}"
                        duration = result.get("duration", 0.0)
                        return video_url, duration

                    if status == "failed":
                        error = result.get("error", "Unknown error")
                        raise ValueError(f"Task failed: {error}")

                except httpx.HTTPStatusError as e:
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        raise ValueError(f"Too many consecutive errors: {e}")
                    logger.warning(f"HTTP error during polling, retrying: {e}")

                await asyncio.sleep(self.poll_interval)

        raise TimeoutError(
            f"Task timed out after {self.max_poll_attempts * self.poll_interval}s"
        )

    async def list_avatars(self) -> List[AvatarInfo]:
        if not self.endpoint_url:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.endpoint_url}/api/avatars",
                )
                if response.status_code != 200:
                    return self._get_default_avatars()

                result = response.json()

            avatars = []
            for avatar in result.get("avatars", []):
                avatars.append(
                    AvatarInfo(
                        avatar_id=avatar.get("id", ""),
                        name=avatar.get("name", ""),
                        preview_url=avatar.get("preview_url"),
                        gender=avatar.get("gender"),
                        style="realistic",
                    )
                )
            return avatars if avatars else self._get_default_avatars()
        except Exception as e:
            logger.warning(f"Failed to fetch SadTalker avatars: {e}")
            return self._get_default_avatars()

    def _get_default_avatars(self) -> List[AvatarInfo]:
        return [
            AvatarInfo(
                avatar_id="default_female",
                name="Default Female",
                preview_url=None,
                gender="female",
                style="realistic",
            ),
            AvatarInfo(
                avatar_id="default_male",
                name="Default Male",
                preview_url=None,
                gender="male",
                style="realistic",
            ),
        ]

    async def list_voices(self) -> List[VoiceInfo]:
        if not self.endpoint_url:
            return self._get_default_voices()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.endpoint_url}/api/voices",
                )
                if response.status_code != 200:
                    return self._get_default_voices()

                result = response.json()

            voices = []
            for voice in result.get("voices", []):
                voices.append(
                    VoiceInfo(
                        voice_id=voice.get("id", ""),
                        name=voice.get("name", ""),
                        language=voice.get("language", "en"),
                        gender=voice.get("gender"),
                    )
                )
            return voices if voices else self._get_default_voices()
        except Exception as e:
            logger.warning(f"Failed to fetch SadTalker voices: {e}")
            return self._get_default_voices()

    def _get_default_voices(self) -> List[VoiceInfo]:
        return [
            VoiceInfo(
                voice_id="en_female_1",
                name="English Female",
                language="en",
                gender="female",
            ),
            VoiceInfo(
                voice_id="en_male_1",
                name="English Male",
                language="en",
                gender="male",
            ),
            VoiceInfo(
                voice_id="ko_female_1",
                name="Korean Female",
                language="ko",
                gender="female",
            ),
            VoiceInfo(
                voice_id="ko_male_1",
                name="Korean Male",
                language="ko",
                gender="male",
            ),
        ]
