"""ElevenLabs TTS adapter implementation."""

import logging
from typing import List

import httpx

from app.services.audio.interfaces import (
    BaseTTSAdapter,
    TTSRequest,
    TTSResult,
    TTSVoiceInfo,
)

logger = logging.getLogger(__name__)

ELEVENLABS_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"


class ElevenLabsTTSAdapter(BaseTTSAdapter):
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    async def generate_speech(self, request: TTSRequest) -> TTSResult:
        if not self._api_key:
            logger.warning("ElevenLabs API key not configured for TTS")
            return TTSResult()

        try:
            voice_id = request.voice_id or ELEVENLABS_DEFAULT_VOICE_ID
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": self._api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": request.text,
                        "model_id": ELEVENLABS_MODEL_ID,
                    },
                )
                response.raise_for_status()
                audio_data = response.content

            return TTSResult(
                audio_data=audio_data,
                metadata={
                    "engine": "elevenlabs",
                    "voice": voice_id,
                    "model": ELEVENLABS_MODEL_ID,
                },
            )
        except Exception as e:
            logger.warning("ElevenLabs TTS generation failed: %s", e)
            return TTSResult()

    async def list_voices(self) -> List[TTSVoiceInfo]:
        if not self._api_key:
            logger.warning("ElevenLabs API key not configured for TTS")
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.elevenlabs.io/v1/voices",
                    headers={"xi-api-key": self._api_key},
                )
                response.raise_for_status()
                data = response.json()

            voices = data.get("voices", [])
            return [
                TTSVoiceInfo(
                    voice_id=voice["voice_id"],
                    name=voice["name"],
                    language=voice.get("labels", {}).get("language", "en"),
                    gender=voice.get("labels", {}).get("gender"),
                    preview_url=voice.get("preview_url"),
                )
                for voice in voices
            ]
        except Exception as e:
            logger.warning("Failed to list ElevenLabs TTS voices: %s", e)
            return []
