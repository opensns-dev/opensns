"""Audio API endpoints for TTS voice listing."""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.auth import get_current_user
from app.core.registry import engine_registry
from app.models.models import User

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/tts/voices")
async def list_tts_voices(
    engine: Optional[str] = Query(
        default=None, description="TTS engine name (e.g., 'openai-tts', 'edge-tts')"
    ),
    user: User = Depends(get_current_user),
):
    """List available TTS voices for the specified or default engine."""
    engine_name = engine or "edge-tts"

    tts_engine = engine_registry.get_tts_engine_or_none(engine_name)
    if not tts_engine:
        return {
            "voices": [],
            "engine": engine_name,
            "error": f"Engine '{engine_name}' not found",
        }

    try:
        voices = await tts_engine.list_voices()
        return {
            "voices": [v.model_dump() for v in voices],
            "engine": engine_name,
            "count": len(voices),
        }
    except Exception as e:
        return {"voices": [], "engine": engine_name, "error": str(e)}
