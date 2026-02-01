from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel


class VideoGenerationRequest(BaseModel):
    images: List[str]
    audio_url: str | None = None
    duration: float = 15.0
    aspect_ratio: str = "9:16"
    transitions: str = "fade"
    music_style: str | None = None


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
