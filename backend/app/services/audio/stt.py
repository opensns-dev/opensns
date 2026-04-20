"""STT adapter implementations."""

import logging

from app.services.audio.interfaces import (
    BaseSTTAdapter,
    STTRequest,
    STTResult,
    STTSegment,
)
from app.services.repurpose.youtube import split_audio

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 24 * 1024 * 1024


class OpenAISTTAdapter(BaseSTTAdapter):
    """OpenAI STT adapter using whisper-1."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key
        self.base_url: str | None = None

    async def transcribe(self, request: STTRequest) -> STTResult:
        if not self._api_key:
            logger.warning("OpenAI API key not configured for STT")
            return STTResult()

        try:
            from openai import AsyncOpenAI

            if self.base_url:
                client = AsyncOpenAI(api_key=self._api_key, base_url=self.base_url)
            else:
                client = AsyncOpenAI(api_key=self._api_key)
            chunks = await split_audio(request.audio_path, MAX_FILE_SIZE)

            all_text_parts: list[str] = []
            all_segments: list[STTSegment] = []
            time_offset = 0.0

            for chunk_path in chunks:
                text, segments, chunk_duration = await self._transcribe_single(
                    client=client,
                    file_path=chunk_path,
                    language=request.language,
                    response_format=request.response_format,
                )
                all_text_parts.append(text)

                for segment in segments:
                    all_segments.append(
                        STTSegment(
                            start=round(segment.start + time_offset, 2),
                            end=round(segment.end + time_offset, 2),
                            text=segment.text,
                        )
                    )

                time_offset += chunk_duration

            return STTResult(
                text="\n".join(all_text_parts),
                segments=all_segments,
                duration=time_offset,
                metadata={"engine": "openai", "model": "whisper-1"},
            )
        except Exception as e:
            logger.warning("OpenAI STT transcription failed: %s", e)
            return STTResult()

    async def _transcribe_single(
        self,
        client,
        file_path: str,
        language: str,
        response_format: str,
    ) -> tuple[str, list[STTSegment], float]:
        with open(file_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                response_format=response_format,
                timestamp_granularities=["segment"],
            )

        text = response.text
        segments: list[STTSegment] = []
        chunk_duration = 0.0

        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                if isinstance(seg, dict):
                    segment = STTSegment(
                        start=seg.get("start", 0),
                        end=seg.get("end", 0),
                        text=seg.get("text", ""),
                    )
                else:
                    segment = STTSegment(
                        start=getattr(seg, "start", 0),
                        end=getattr(seg, "end", 0),
                        text=getattr(seg, "text", ""),
                    )
                segments.append(segment)

            last = segments[-1] if segments else None
            if last:
                chunk_duration = last.end

        if not chunk_duration and hasattr(response, "duration"):
            chunk_duration = response.duration or 0.0

        return text, segments, chunk_duration