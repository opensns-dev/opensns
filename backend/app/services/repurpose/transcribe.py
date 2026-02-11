import json
import logging
import os

from openai import AsyncOpenAI

from app.services.repurpose.youtube import split_audio

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 24 * 1024 * 1024


async def transcribe_audio(
    audio_path: str,
    api_key: str,
    base_url: str | None = None,
    language: str = "ko",
) -> tuple[str, list[dict]]:
    """
    Transcribe audio using OpenAI-compatible Whisper API.
    Returns (full_text, segments) where segments = [{start, end, text}, ...].
    Handles chunking for files > 24MB automatically.
    """
    client_kwargs: dict = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = AsyncOpenAI(**client_kwargs)

    chunks = await split_audio(audio_path, MAX_FILE_SIZE)

    all_text_parts: list[str] = []
    all_segments: list[dict] = []
    time_offset = 0.0

    for chunk_path in chunks:
        text, segments, chunk_duration = await _transcribe_single(
            client, chunk_path, language
        )
        all_text_parts.append(text)

        for seg in segments:
            all_segments.append(
                {
                    "start": round(seg["start"] + time_offset, 2),
                    "end": round(seg["end"] + time_offset, 2),
                    "text": seg["text"],
                }
            )

        time_offset += chunk_duration

    full_text = "\n".join(all_text_parts)
    return full_text, all_segments


async def _transcribe_single(
    client: AsyncOpenAI,
    file_path: str,
    language: str,
) -> tuple[str, list[dict], float]:
    with open(file_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    text = response.text
    segments = []
    chunk_duration = 0.0

    if hasattr(response, "segments") and response.segments:
        for seg in response.segments:
            seg_dict = {
                "start": seg.get("start", 0)
                if isinstance(seg, dict)
                else getattr(seg, "start", 0),
                "end": seg.get("end", 0)
                if isinstance(seg, dict)
                else getattr(seg, "end", 0),
                "text": seg.get("text", "")
                if isinstance(seg, dict)
                else getattr(seg, "text", ""),
            }
            segments.append(seg_dict)

        last = segments[-1] if segments else None
        if last:
            chunk_duration = last["end"]

    if not chunk_duration and hasattr(response, "duration"):
        chunk_duration = response.duration or 0.0

    return text, segments, chunk_duration
