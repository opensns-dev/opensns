"""Background music adapter implementations."""

import logging
import random
from pathlib import Path
from typing import List, Optional

from app.services.audio.interfaces import BaseMusicAdapter, MusicRequest, MusicResult

logger = logging.getLogger(__name__)

# Base directory for bundled BGM tracks
BGM_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "bgm"

# Style-to-filename mapping for bundled tracks
# Filenames follow pattern: {style}.mp3
STYLE_MAP = {
    "upbeat": "upbeat.mp3",
    "corporate": "corporate.mp3",
    "emotional": "emotional.mp3",
    "minimal": "minimal.mp3",
    "energetic": "energetic.mp3",
}

DEFAULT_STYLE = "corporate"


class StaticBGMAdapter(BaseMusicAdapter):
    """BGM adapter that serves from a bundled library of royalty-free tracks."""

    def __init__(self):
        pass

    async def generate_music(self, request: MusicRequest) -> MusicResult:
        style = request.style or DEFAULT_STYLE
        filename = STYLE_MAP.get(style)

        if not filename:
            # Pick a random track if style not found
            available = list(STYLE_MAP.values())
            if not available:
                logger.warning("No BGM tracks available")
                return MusicResult()
            filename = random.choice(available)

        filepath = BGM_DIR / filename
        if not filepath.exists():
            logger.warning("BGM file not found: %s", filepath)
            return MusicResult()

        try:
            audio_data = filepath.read_bytes()
            return MusicResult(
                audio_data=audio_data,
                metadata={"engine": "static-bgm", "style": style, "filename": filename},
            )
        except Exception as e:
            logger.warning("Failed to read BGM file: %s", e)
            return MusicResult()

    async def list_styles(self) -> List[str]:
        return list(STYLE_MAP.keys())
