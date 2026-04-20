"""ElevenLabs music adapter."""

import logging
from typing import List

import httpx

from app.services.audio.interfaces import BaseMusicAdapter, MusicRequest, MusicResult

logger = logging.getLogger(__name__)


class ElevenLabsMusicAdapter(BaseMusicAdapter):
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    async def generate_music(self, request: MusicRequest) -> MusicResult:
        if not self._api_key:
            logger.warning("ElevenLabs Music API key not configured")
            return MusicResult()

        try:
            prompt = request.prompt or request.style or "ambient background music"
            payload = {
                "prompt": prompt,
                "duration_seconds": int(request.duration),
            }
            headers = {
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.elevenlabs.io/v1/music",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                audio_data = response.content

            return MusicResult(
                audio_data=audio_data,
                metadata={
                    "engine": "elevenlabs-music",
                    "prompt": prompt,
                    "duration": request.duration,
                    "format": request.output_format,
                },
            )
        except Exception as e:
            logger.warning("ElevenLabs Music generation failed: %s", e)
            return MusicResult()

    async def list_styles(self) -> List[str]:
        return ["pop", "rock", "electronic", "ambient", "cinematic", "jazz", "classical"]
