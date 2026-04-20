import logging

from app.services.audio.interfaces import STTRequest
from app.services.audio.stt import OpenAISTTAdapter

logger = logging.getLogger(__name__)


async def transcribe_audio(
    audio_path: str,
    api_key: str,
    base_url: str | None = None,
    language: str = "ko",
) -> tuple[str, list[dict]]:
    """Transcribe audio using OpenAI-compatible Whisper API.
    Returns (full_text, segments) where segments = [{start, end, text}, ...].
    Handles chunking for files > 24MB automatically.
    """
    adapter = OpenAISTTAdapter(api_key=api_key)
    adapter.base_url = base_url
    result = await adapter.transcribe(
        STTRequest(audio_path=audio_path, language=language)
    )

    segments = [
        {"start": seg.start, "end": seg.end, "text": seg.text}
        for seg in result.segments
    ]
    return result.text, segments