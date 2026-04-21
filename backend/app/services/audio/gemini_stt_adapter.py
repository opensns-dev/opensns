"""Google Gemini STT adapter."""

import base64
import logging
import mimetypes
from pathlib import Path

import httpx

from app.core.exceptions import APIKeyNotConfiguredError
from app.services.audio.interfaces import (
    BaseSTTAdapter,
    STTRequest,
    STTResult,
)

logger = logging.getLogger(__name__)

MIME_FALLBACK = "audio/mpeg"


class GeminiSTTAdapter(BaseSTTAdapter):
    """Speech-to-text via Gemini audio understanding."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def transcribe(self, request: STTRequest) -> STTResult:
        if not self.api_key:
            raise APIKeyNotConfiguredError("Google Gemini STT")

        audio_path = Path(request.audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {request.audio_path}")

        file_size = audio_path.stat().st_size
        max_size = 20 * 1024 * 1024
        if file_size > max_size:
            raise ValueError(
                f"Audio file too large for inline upload "
                f"({file_size // (1024 * 1024)}MB). Max: 20MB"
            )

        audio_bytes = audio_path.read_bytes()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        mime_type, _ = mimetypes.guess_type(str(audio_path))
        if not mime_type or not mime_type.startswith("audio/"):
            mime_type = MIME_FALLBACK

        language_instruction = ""
        if request.language:
            language_instruction = f" The audio is in {request.language} language."

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Transcribe this audio exactly, word for word. "
                                "Output only the transcribed text, nothing else."
                                f"{language_instruction}"
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": audio_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.0},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        return STTResult(
            text=text.strip(),
            segments=[],
            metadata={
                "engine": "gemini-stt",
                "model": self.model,
                "language": request.language,
            },
        )

    async def supported_languages(self) -> list[str]:
        return [
            "ko", "en", "ja", "zh", "es", "fr", "de", "pt", "it", "ru",
            "ar", "hi", "th", "vi", "id", "tr", "pl", "nl", "sv",
        ]
