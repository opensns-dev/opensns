from app.core.registry import engine_registry
from app.services.fallback_llm import FallbackLLMAdapter
from app.services.openai_adapter import OpenAIAdapter
from app.services.ollama_adapter import OllamaAdapter
from app.services.image.comfyui_adapter import ComfyUIAdapter
from app.services.image.fal_adapter import FalAIAdapter, FluxProAdapter
from app.services.video.fal_video_adapter import FalVideoAdapter, RunwayAdapter
from app.services.video.comfyui_video_adapter import ComfyUIVideoAdapter
from app.services.video.heygen_adapter import HeyGenAdapter
from app.services.video.did_adapter import DIDAdapter
from app.services.video.sadtalker_adapter import SadTalkerAdapter
from app.core.config import settings


def register_engines():
    engine_registry.register_llm_engine("fallback", FallbackLLMAdapter)
    engine_registry.register_llm_engine(
        "openai", lambda: OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
    )
    engine_registry.register_llm_engine("ollama", lambda: OllamaAdapter())

    engine_registry.register_image_engine("comfyui", lambda: ComfyUIAdapter())
    engine_registry.register_image_engine(
        "fal", lambda: FalAIAdapter(api_key=settings.FAL_KEY)
    )
    engine_registry.register_image_engine(
        "flux-pro", lambda: FluxProAdapter(api_key=settings.FAL_KEY)
    )

    engine_registry.register_video_engine(
        "fal-video", lambda: FalVideoAdapter(api_key=settings.FAL_KEY)
    )
    engine_registry.register_video_engine(
        "runway", lambda: RunwayAdapter(api_key=settings.FAL_KEY)
    )
    engine_registry.register_video_engine(
        "comfyui-video", lambda: ComfyUIVideoAdapter()
    )
    engine_registry.register_video_engine(
        "heygen", lambda: HeyGenAdapter(api_key=settings.HEYGEN_API_KEY)
    )
    engine_registry.register_video_engine(
        "d-id", lambda: DIDAdapter(api_key=settings.DID_API_KEY)
    )
    engine_registry.register_video_engine(
        "sadtalker", lambda: SadTalkerAdapter(endpoint_url=settings.SADTALKER_URL)
    )
