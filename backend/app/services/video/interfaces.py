from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel, field_validator

MAX_SCRIPT_LENGTH = 1500


class VideoGenerationRequest(BaseModel):
    images: List[str]
    audio_url: str | None = None
    duration: float = 15.0
    aspect_ratio: str = "9:16"
    transitions: str = "fade"
    music_style: str | None = None


class UGCVideoRequest(BaseModel):
    """Request for UGC (User-Generated Content) talking head video generation."""

    script: str
    avatar_id: str | None = None
    voice_id: str | None = None
    language: str = "en"
    aspect_ratio: str = "9:16"
    duration_limit: float | None = None
    background_color: str | None = None
    background_image_url: str | None = None

    @field_validator("script")
    @classmethod
    def validate_script_length(cls, v: str) -> str:
        if len(v) > MAX_SCRIPT_LENGTH:
            raise ValueError(
                f"Script exceeds maximum length of {MAX_SCRIPT_LENGTH} characters "
                f"(got {len(v)}). Please shorten your script."
            )
        if len(v.strip()) == 0:
            raise ValueError("Script cannot be empty")
        return v


class AvatarInfo(BaseModel):
    """Information about an available avatar."""

    avatar_id: str
    name: str
    preview_url: str | None = None
    gender: str | None = None
    style: str | None = None  # e.g., "realistic", "animated"


class VoiceInfo(BaseModel):
    """Information about an available voice."""

    voice_id: str
    name: str
    language: str
    gender: str | None = None
    preview_url: str | None = None


class VideoGenerationResult(BaseModel):
    video_url: str | None = None
    video_data: bytes | None = None
    duration: float = 0.0
    metadata: Dict[str, Any] = {}


class BaseVideoAdapter(ABC):
    @abstractmethod
    async def generate_video(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResult:
        pass

    @abstractmethod
    async def image_to_video(
        self, image_url: str, motion_prompt: str, duration: float = 5.0
    ) -> VideoGenerationResult:
        pass

    async def generate_ugc_video(
        self, request: UGCVideoRequest
    ) -> VideoGenerationResult:
        """Generate UGC talking head video. Override in UGC-capable adapters."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support UGC video generation"
        )

    async def list_avatars(self) -> List[AvatarInfo]:
        """List available avatars. Override in UGC-capable adapters."""
        return []

    async def list_voices(self) -> List[VoiceInfo]:
        """List available voices. Override in UGC-capable adapters."""
        return []

    def supports_ugc(self) -> bool:
        """Check if this adapter supports UGC video generation."""
        return False
