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


class DIDAdapter(BaseVideoAdapter):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.DID_API_KEY
        self.base_url = "https://api.d-id.com"
        self.poll_interval = 5.0
        self.max_poll_attempts = 120

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def supports_ugc(self) -> bool:
        return True

    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        raise NotImplementedError(
            "D-ID specializes in UGC video generation. Use generate_ugc_video() instead."
        )

    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        raise NotImplementedError(
            "D-ID specializes in UGC video generation. Use generate_ugc_video() instead."
        )

    async def generate_ugc_video(
        self, request: UGCVideoRequest
    ) -> VideoGenerationResult:
        if not self.api_key:
            raise ValueError("DID_API_KEY is not configured")

        source_url = request.background_image_url or await self._get_default_presenter()

        talk_payload = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "input": request.script,
                "provider": {
                    "type": "microsoft",
                    "voice_id": request.voice_id or "en-US-JennyNeural",
                },
            },
            "config": {
                "stitch": True,
                "result_format": "mp4",
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/talks",
                headers=self._get_headers(),
                json=talk_payload,
            )
            response.raise_for_status()
            result = response.json()

        talk_id = result.get("id")
        if not talk_id:
            raise ValueError(f"Failed to create talk: {result}")

        video_url, duration = await self._poll_talk_status(talk_id)

        return VideoGenerationResult(
            video_url=video_url,
            duration=duration,
            metadata={
                "engine": "d-id",
                "talk_id": talk_id,
                "voice_id": request.voice_id,
                "script": request.script[:100],
            },
        )

    async def _poll_talk_status(self, talk_id: str) -> tuple[str, float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            consecutive_errors = 0
            for _ in range(self.max_poll_attempts):
                try:
                    response = await client.get(
                        f"{self.base_url}/talks/{talk_id}",
                        headers=self._get_headers(),
                    )
                    response.raise_for_status()
                    result = response.json()
                    consecutive_errors = 0

                    status = result.get("status")

                    if status == "done":
                        video_url = result.get("result_url")
                        duration = result.get("duration", 0.0)
                        return video_url, duration

                    if status == "error":
                        error = result.get("error", {}).get(
                            "description", "Unknown error"
                        )
                        raise ValueError(f"Talk generation failed: {error}")

                except httpx.HTTPStatusError as e:
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        raise ValueError(f"Too many consecutive errors: {e}")
                    logger.warning(f"HTTP error during polling, retrying: {e}")

                await asyncio.sleep(self.poll_interval)

        raise TimeoutError(
            f"Talk generation timed out after {self.max_poll_attempts * self.poll_interval}s"
        )

    async def _get_default_presenter(self) -> str:
        return "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg"

    async def list_avatars(self) -> List[AvatarInfo]:
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/clips/presenters",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            avatars = []
            for presenter in result.get("presenters", []):
                avatars.append(
                    AvatarInfo(
                        avatar_id=presenter.get("presenter_id", ""),
                        name=presenter.get("name", ""),
                        preview_url=presenter.get("thumbnail_url"),
                        gender=presenter.get("gender"),
                        style="realistic",
                    )
                )
            return avatars
        except Exception as e:
            logger.warning(f"Failed to fetch D-ID presenters: {e}")
            return []

    async def list_voices(self) -> List[VoiceInfo]:
        voices = [
            VoiceInfo(
                voice_id="en-US-JennyNeural",
                name="Jenny (US)",
                language="en-US",
                gender="female",
            ),
            VoiceInfo(
                voice_id="en-US-GuyNeural",
                name="Guy (US)",
                language="en-US",
                gender="male",
            ),
            VoiceInfo(
                voice_id="en-GB-SoniaNeural",
                name="Sonia (UK)",
                language="en-GB",
                gender="female",
            ),
            VoiceInfo(
                voice_id="ko-KR-SunHiNeural",
                name="Sun-Hi (Korea)",
                language="ko-KR",
                gender="female",
            ),
            VoiceInfo(
                voice_id="ko-KR-InJoonNeural",
                name="InJoon (Korea)",
                language="ko-KR",
                gender="male",
            ),
            VoiceInfo(
                voice_id="ja-JP-NanamiNeural",
                name="Nanami (Japan)",
                language="ja-JP",
                gender="female",
            ),
            VoiceInfo(
                voice_id="ja-JP-KeitaNeural",
                name="Keita (Japan)",
                language="ja-JP",
                gender="male",
            ),
            VoiceInfo(
                voice_id="zh-CN-XiaoxiaoNeural",
                name="Xiaoxiao (China)",
                language="zh-CN",
                gender="female",
            ),
        ]
        return voices
