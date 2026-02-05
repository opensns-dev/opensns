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


class HeyGenAdapter(BaseVideoAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.HEYGEN_API_KEY
        self.base_url = "https://api.heygen.com"
        self.poll_interval = 5.0
        self.max_poll_attempts = 120

    def _get_headers(self) -> dict:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def supports_ugc(self) -> bool:
        return True

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        raise NotImplementedError(
            "HeyGen specializes in UGC video generation. Use generate_ugc_video() instead."
        )

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        raise NotImplementedError(
            "HeyGen specializes in UGC video generation. Use generate_ugc_video() instead."
        )

    async def generate_ugc_video(
        self, request: UGCVideoRequest
    ) -> VideoGenerationResult:
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY is not configured")

        avatar_id = request.avatar_id or await self._get_default_avatar_id()
        voice_id = request.voice_id or await self._get_default_voice_id(
            request.language
        )

        video_payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "text",
                        "input_text": request.script,
                        "voice_id": voice_id,
                    },
                }
            ],
            "dimension": self._parse_dimension(request.aspect_ratio),
        }

        if request.background_color:
            video_payload["video_inputs"][0]["background"] = {
                "type": "color",
                "value": request.background_color,
            }
        elif request.background_image_url:
            video_payload["video_inputs"][0]["background"] = {
                "type": "image",
                "url": request.background_image_url,
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v2/video/generate",
                headers=self._get_headers(),
                json=video_payload,
            )
            response.raise_for_status()
            result = response.json()

        video_id = result.get("data", {}).get("video_id")
        if not video_id:
            raise ValueError(f"Failed to create video: {result}")

        video_url, duration = await self._poll_video_status(video_id)

        return VideoGenerationResult(
            video_url=video_url,
            duration=duration,
            metadata={
                "engine": "heygen",
                "video_id": video_id,
                "avatar_id": avatar_id,
                "voice_id": voice_id,
                "script": request.script[:100],
            },
        )

    async def _poll_video_status(self, video_id: str) -> tuple[str, float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            consecutive_errors = 0
            for _ in range(self.max_poll_attempts):
                try:
                    response = await client.get(
                        f"{self.base_url}/v1/video_status.get",
                        headers=self._get_headers(),
                        params={"video_id": video_id},
                    )
                    response.raise_for_status()
                    result = response.json()
                    consecutive_errors = 0

                    status = result.get("data", {}).get("status")

                    if status == "completed":
                        video_url = result.get("data", {}).get("video_url")
                        duration = result.get("data", {}).get("duration", 0.0)
                        return video_url, duration

                    if status == "failed":
                        error = result.get("data", {}).get("error", "Unknown error")
                        raise ValueError(f"Video generation failed: {error}")

                except httpx.HTTPStatusError as e:
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        raise ValueError(f"Too many consecutive errors: {e}")
                    logger.warning(f"HTTP error during polling, retrying: {e}")

                await asyncio.sleep(self.poll_interval)

        raise TimeoutError(
            f"Video generation timed out after {self.max_poll_attempts * self.poll_interval}s"
        )

    def _parse_dimension(self, aspect_ratio: str) -> dict:
        dimensions = {
            "9:16": {"width": 720, "height": 1280},
            "16:9": {"width": 1280, "height": 720},
            "1:1": {"width": 1080, "height": 1080},
        }
        return dimensions.get(aspect_ratio, dimensions["9:16"])

    async def _get_default_avatar_id(self) -> str:
        avatars = await self.list_avatars()
        if avatars:
            return avatars[0].avatar_id
        return "Daisy-inskirt-20220818"

    async def _get_default_voice_id(self, language: str) -> str:
        voices = await self.list_voices()
        for voice in voices:
            if voice.language.startswith(language):
                return voice.voice_id
        return "en-US-JennyNeural"

    async def list_avatars(self) -> List[AvatarInfo]:
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/v2/avatars",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            avatars = []
            for avatar_data in result.get("data", {}).get("avatars", []):
                avatars.append(
                    AvatarInfo(
                        avatar_id=avatar_data.get("avatar_id", ""),
                        name=avatar_data.get("avatar_name", ""),
                        preview_url=avatar_data.get("preview_image_url"),
                        gender=avatar_data.get("gender"),
                        style=avatar_data.get("avatar_style"),
                    )
                )
            return avatars
        except Exception as e:
            logger.warning(f"Failed to fetch HeyGen avatars: {e}")
            return []

    async def list_voices(self) -> List[VoiceInfo]:
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/v2/voices",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            voices = []
            for voice_data in result.get("data", {}).get("voices", []):
                voices.append(
                    VoiceInfo(
                        voice_id=voice_data.get("voice_id", ""),
                        name=voice_data.get("display_name", ""),
                        language=voice_data.get("language", ""),
                        gender=voice_data.get("gender"),
                        preview_url=voice_data.get("preview_audio"),
                    )
                )
            return voices
        except Exception as e:
            logger.warning(f"Failed to fetch HeyGen voices: {e}")
            return []
