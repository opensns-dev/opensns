"""Google Gemini TTS adapter."""

import base64
import logging
import struct
from typing import List

import httpx

from app.core.exceptions import APIKeyNotConfiguredError
from app.services.audio.interfaces import (
    BaseTTSAdapter,
    TTSRequest,
    TTSResult,
    TTSVoiceInfo,
)

logger = logging.getLogger(__name__)

GEMINI_TTS_VOICES = [
    TTSVoiceInfo(voice_id="Zephyr", name="Zephyr", language="en", gender="neutral"),
    TTSVoiceInfo(voice_id="Puck", name="Puck", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Charon", name="Charon", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Kore", name="Kore", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Fenrir", name="Fenrir", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Leda", name="Leda", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Orus", name="Orus", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Aoede", name="Aoede", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Callirrhoe", name="Callirrhoe", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Autonoe", name="Autonoe", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Enceladus", name="Enceladus", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Iapetus", name="Iapetus", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Umbriel", name="Umbriel", language="en", gender="neutral"),
    TTSVoiceInfo(voice_id="Algieba", name="Algieba", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Despina", name="Despina", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Erinome", name="Erinome", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Algenib", name="Algenib", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Rasalgethi", name="Rasalgethi", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Laomedeia", name="Laomedeia", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Achernar", name="Achernar", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Alnilam", name="Alnilam", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Schedar", name="Schedar", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Gacrux", name="Gacrux", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Pulcherrima", name="Pulcherrima", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Achird", name="Achird", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Zubenelgenubi", name="Zubenelgenubi", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Vindemiatrix", name="Vindemiatrix", language="en", gender="female"),
    TTSVoiceInfo(voice_id="Sadachbia", name="Sadachbia", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Sadaltager", name="Sadaltager", language="en", gender="male"),
    TTSVoiceInfo(voice_id="Sulafat", name="Sulafat", language="en", gender="female"),
]

PCM_SAMPLE_RATE = 24000
PCM_CHANNELS = 1
PCM_BITS_PER_SAMPLE = 16


def _pcm_to_wav(pcm_data: bytes) -> bytes:
    """Wrap raw PCM (24kHz mono s16le) in a WAV header."""
    data_size = len(pcm_data)
    byte_rate = PCM_SAMPLE_RATE * PCM_CHANNELS * PCM_BITS_PER_SAMPLE // 8
    block_align = PCM_CHANNELS * PCM_BITS_PER_SAMPLE // 8

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        PCM_CHANNELS,
        PCM_SAMPLE_RATE,
        byte_rate,
        block_align,
        PCM_BITS_PER_SAMPLE,
        b"data",
        data_size,
    )
    return header + pcm_data


class GeminiTTSAdapter(BaseTTSAdapter):
    """Text-to-speech via Gemini TTS model."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash-preview-tts",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_speech(self, request: TTSRequest) -> TTSResult:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Gemini TTS")

        voice_name = request.voice_id or "Kore"

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": request.text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name}
                    }
                },
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        inline_data = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("inlineData", {})
        )

        audio_b64 = inline_data.get("data")
        if not audio_b64:
            raise RuntimeError("No audio data in Gemini TTS response")

        pcm_bytes = base64.b64decode(audio_b64)
        wav_bytes = _pcm_to_wav(pcm_bytes)

        return TTSResult(
            audio_data=wav_bytes,
            metadata={
                "engine": "gemini-tts",
                "model": self.model,
                "voice": voice_name,
                "format": "wav",
                "sample_rate": PCM_SAMPLE_RATE,
            },
        )

    async def list_voices(self) -> List[TTSVoiceInfo]:
        return GEMINI_TTS_VOICES
