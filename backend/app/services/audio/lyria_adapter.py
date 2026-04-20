"""Google Lyria music adapter."""

import base64
import logging
from typing import List

import httpx

from app.services.audio.interfaces import BaseMusicAdapter, MusicRequest, MusicResult

logger = logging.getLogger(__name__)


class LyriaAdapter(BaseMusicAdapter):
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    async def generate_music(self, request: MusicRequest) -> MusicResult:
        if not self._api_key:
            logger.warning("Google Lyria API key not configured")
            return MusicResult()

        try:
            prompt = request.prompt or request.style or "ambient background music"
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"lyria-3-clip-preview:generateContent?key={self._api_key}"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    f"Generate background music: {prompt}, duration {int(request.duration)}s"
                                )
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {"voiceName": "Aoede"}
                        }
                    },
                },
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            inline_data = data["candidates"][0]["content"]["parts"][0]["inlineData"]
            audio_data = base64.b64decode(inline_data["data"])
            mime_type = inline_data.get("mimeType")

            return MusicResult(
                audio_data=audio_data,
                metadata={
                    "engine": "lyria",
                    "prompt": prompt,
                    "duration": request.duration,
                    "mime_type": mime_type,
                },
            )
        except Exception as e:
            logger.warning("Google Lyria generation failed: %s", e)
            return MusicResult()

    async def list_styles(self) -> List[str]:
        return [
            "upbeat",
            "corporate",
            "emotional",
            "minimal",
            "energetic",
            "ambient",
            "cinematic",
        ]
