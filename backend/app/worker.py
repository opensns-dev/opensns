"""TaskIQ worker for CPU-heavy audio processing tasks.

Run with: taskiq worker app.worker:broker --workers 2 --fs-discover

This module defines the TaskIQ broker and background tasks for audio mixing.
The worker process runs separately from the FastAPI backend, sharing the same
codebase but executing CPU-intensive ffmpeg operations off the main event loop.
"""

import logging

from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from app.core.config import settings

logger = logging.getLogger(__name__)

result_backend = RedisAsyncResultBackend(
    redis_url=settings.REDIS_URL,
    result_ex_time=3600,
)

broker = ListQueueBroker(
    url=settings.REDIS_URL,
).with_result_backend(result_backend)


@broker.task(task_name="health_check")
async def health_check_task() -> dict:
    """Smoke-test task to verify worker connectivity."""
    return {"status": "ok", "worker": "audio"}


@broker.task(task_name="mix_audio", timeout=300, retry_on_error=False)
async def mix_audio_task(spec: dict) -> dict:
    """Mix narration and/or BGM audio into a video file.

    Args:
        spec: Dict with keys matching AudioMixRequest fields:
            - video_url: str
            - narration_url: str | None
            - bgm_url: str | None
            - narration_volume: float (default 1.0)
            - bgm_volume: float (default 0.15)
            - ducking_enabled: bool (default True)

    Returns:
        Dict with mixed video data or error info.
    """
    from app.services.audio.interfaces import AudioMixRequest
    from app.services.audio.mixer import ffmpeg_mix_audio

    request = AudioMixRequest(**spec)
    result = await ffmpeg_mix_audio(request)

    if result.video_data:
        import base64

        video_data_b64 = base64.b64encode(result.video_data).decode()
        return {
            "success": True,
            "video_data_b64": video_data_b64,
            "video_url": f"data:video/mp4;base64,{video_data_b64}",
            "metadata": result.metadata,
        }

    return {
        "success": False,
        "error": "Audio mixing produced no output",
        "metadata": result.metadata,
    }
