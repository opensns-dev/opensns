"""Abstract base classes and models for audio adapters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TTSVoiceInfo(BaseModel):
    """Information about an available TTS voice."""

    voice_id: str
    name: str
    language: str
    gender: Optional[str] = None
    preview_url: Optional[str] = None


class TTSRequest(BaseModel):
    """Request to generate speech from text."""

    text: str
    voice_id: Optional[str] = None
    language: str = "en"
    speed: float = 1.0
    output_format: str = "mp3"


class TTSResult(BaseModel):
    """Result from TTS generation."""

    audio_url: Optional[str] = None
    audio_data: Optional[bytes] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class MusicRequest(BaseModel):
    """Request for background music."""

    prompt: Optional[str] = None
    style: Optional[str] = None
    duration: float = 15.0
    output_format: str = "mp3"


class MusicResult(BaseModel):
    """Result from music generation."""

    audio_url: Optional[str] = None
    audio_data: Optional[bytes] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class AudioMixRequest(BaseModel):
    """Request to mix audio tracks with a video."""

    video_url: str
    narration_url: Optional[str] = None
    bgm_url: Optional[str] = None
    narration_volume: float = 1.0
    bgm_volume: float = 0.15
    ducking_enabled: bool = True
    preserve_original_audio: bool = False


class AudioMixResult(BaseModel):
    """Result from audio mixing."""

    video_url: Optional[str] = None
    video_data: Optional[bytes] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class BaseTTSAdapter(ABC):
    """Abstract base class for Text-to-Speech adapters."""

    @abstractmethod
    async def generate_speech(self, request: TTSRequest) -> TTSResult:
        """Generate speech audio from text."""
        pass

    @abstractmethod
    async def list_voices(self) -> List[TTSVoiceInfo]:
        """List available voices for this TTS engine."""
        pass


class BaseMusicAdapter(ABC):
    """Abstract base class for background music adapters."""

    @abstractmethod
    async def generate_music(self, request: MusicRequest) -> MusicResult:
        """Generate or select background music."""
        pass

    async def list_styles(self) -> List[str]:
        """List available music styles. Override in subclasses."""
        return []
