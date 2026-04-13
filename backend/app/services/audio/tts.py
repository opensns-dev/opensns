"""TTS adapter implementations."""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from app.services.audio.interfaces import (
    BaseTTSAdapter,
    TTSRequest,
    TTSResult,
    TTSVoiceInfo,
)

logger = logging.getLogger(__name__)

OPENAI_VOICES = [
    TTSVoiceInfo(voice_id="alloy", name="Alloy", language="en", gender="neutral"),
    TTSVoiceInfo(voice_id="echo", name="Echo", language="en", gender="male"),
    TTSVoiceInfo(voice_id="fable", name="Fable", language="en", gender="neutral"),
    TTSVoiceInfo(voice_id="nova", name="Nova", language="en", gender="female"),
    TTSVoiceInfo(voice_id="onyx", name="Onyx", language="en", gender="male"),
    TTSVoiceInfo(voice_id="shimmer", name="Shimmer", language="en", gender="female"),
]


class OpenAITTSAdapter(BaseTTSAdapter):
    """OpenAI TTS adapter using gpt-4o-mini-tts model."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key

    async def generate_speech(self, request: TTSRequest) -> TTSResult:
        if not self._api_key:
            logger.warning("OpenAI API key not configured for TTS")
            return TTSResult()

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key)
            response = await client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=request.voice_id or "nova",
                input=request.text,
                response_format="mp3",
                speed=request.speed,
            )
            audio_data = response.content
            return TTSResult(
                audio_data=audio_data,
                metadata={
                    "engine": "openai",
                    "voice": request.voice_id or "nova",
                    "model": "gpt-4o-mini-tts",
                },
            )
        except Exception as e:
            logger.warning("OpenAI TTS generation failed: %s", e)
            return TTSResult()

    async def list_voices(self) -> List[TTSVoiceInfo]:
        return OPENAI_VOICES


class EdgeTTSAdapter(BaseTTSAdapter):
    """Edge TTS adapter using Microsoft Edge's free TTS service."""

    def __init__(self):
        pass

    async def generate_speech(self, request: TTSRequest) -> TTSResult:
        try:
            import edge_tts

            voice = request.voice_id or "en-US-AriaNeural"
            communicate = edge_tts.Communicate(
                request.text, voice, rate=self._speed_to_rate(request.speed)
            )

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)

            audio_data = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)

            return TTSResult(
                audio_data=audio_data,
                metadata={"engine": "edge-tts", "voice": voice},
            )
        except Exception as e:
            logger.warning("Edge TTS generation failed: %s", e)
            return TTSResult()

    async def list_voices(self) -> List[TTSVoiceInfo]:
        try:
            import edge_tts

            voices = await edge_tts.list_voices()
            return [
                TTSVoiceInfo(
                    voice_id=v["ShortName"],
                    name=v["FriendlyName"],
                    language=v["Locale"],
                    gender=v.get("Gender", "").lower() or None,
                )
                for v in voices
            ]
        except Exception as e:
            logger.warning("Failed to list Edge TTS voices: %s", e)
            return []

    @staticmethod
    def _speed_to_rate(speed: float) -> str:
        """Convert speed multiplier to Edge TTS rate string."""
        pct = int((speed - 1.0) * 100)
        if pct >= 0:
            return f"+{pct}%"
        return f"{pct}%"
