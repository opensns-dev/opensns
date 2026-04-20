from app.core.registry import engine_registry
from app.services.fallback_llm import FallbackLLMAdapter
from app.services.openai_adapter import OpenAIAdapter
from app.services.openrouter_adapter import OpenRouterAdapter
from app.services.anthropic_adapter import AnthropicAdapter
from app.services.gemini_adapter import GeminiAdapter
from app.services.groq_adapter import GroqAdapter
from app.services.ollama_adapter import OllamaAdapter
from app.services.image.comfyui_adapter import ComfyUIAdapter
from app.services.image.fal_adapter import FalAIAdapter, FluxProAdapter
from app.services.image.openrouter_image_adapter import OpenRouterImageAdapter
from app.services.image.openai_image_adapter import OpenAIImageAdapter
from app.services.image.replicate_adapter import ReplicateAdapter
from app.services.image.together_adapter import TogetherImageAdapter
from app.services.image.stability_adapter import StabilityAdapter
from app.services.image.bfl_adapter import BFLAdapter
from app.services.image.leonardo_adapter import LeonardoAdapter
from app.services.image.ideogram_adapter import IdeogramAdapter
from app.services.video.fal_video_adapter import FalVideoAdapter, RunwayAdapter
from app.services.video.comfyui_video_adapter import ComfyUIVideoAdapter
from app.services.video.heygen_adapter import HeyGenAdapter
from app.services.video.did_adapter import DIDAdapter
from app.services.video.sadtalker_adapter import SadTalkerAdapter
from app.services.audio.tts import OpenAITTSAdapter, EdgeTTSAdapter
from app.services.audio.elevenlabs_tts import ElevenLabsTTSAdapter
from app.services.audio.stt import OpenAISTTAdapter
from app.services.audio.bgm import StaticBGMAdapter
from app.services.audio.lyria_adapter import LyriaAdapter
from app.services.audio.elevenlabs_music_adapter import ElevenLabsMusicAdapter
from app.services.audio.mubert_adapter import MubertAdapter
from app.core.config import settings


def register_engines():
    engine_registry.register_llm_engine("fallback", FallbackLLMAdapter)
    engine_registry.register_llm_engine(
        "openai", lambda: OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
    )
    engine_registry.register_llm_engine(
        "anthropic", lambda: AnthropicAdapter(api_key=settings.ANTHROPIC_API_KEY)
    )
    engine_registry.register_llm_engine(
        "gemini", lambda: GeminiAdapter(api_key=settings.GOOGLE_API_KEY)
    )
    engine_registry.register_llm_engine(
        "groq", lambda: GroqAdapter(api_key=settings.GROQ_API_KEY)
    )
    engine_registry.register_llm_engine(
        "openrouter",
        lambda: OpenRouterAdapter(api_key=settings.OPENROUTER_API_KEY),
    )
    engine_registry.register_llm_engine("ollama", lambda: OllamaAdapter())

    engine_registry.register_image_engine("comfyui", lambda: ComfyUIAdapter())
    engine_registry.register_image_engine(
        "fal", lambda: FalAIAdapter(api_key=settings.FAL_KEY)
    )
    engine_registry.register_image_engine(
        "flux-pro", lambda: FluxProAdapter(api_key=settings.FAL_KEY)
    )
    engine_registry.register_image_engine(
        "openrouter-image",
        lambda: OpenRouterImageAdapter(api_key=settings.OPENROUTER_API_KEY),
    )
    engine_registry.register_image_engine(
        "openai-image",
        lambda: OpenAIImageAdapter(api_key=settings.OPENAI_API_KEY),
    )
    engine_registry.register_image_engine(
        "replicate",
        lambda: ReplicateAdapter(api_key=settings.REPLICATE_API_TOKEN),
    )
    engine_registry.register_image_engine(
        "together",
        lambda: TogetherImageAdapter(api_key=settings.TOGETHER_API_KEY),
    )
    engine_registry.register_image_engine(
        "stability",
        lambda: StabilityAdapter(api_key=settings.STABILITY_API_KEY),
    )
    engine_registry.register_image_engine(
        "bfl",
        lambda: BFLAdapter(api_key=settings.BFL_API_KEY),
    )
    engine_registry.register_image_engine(
        "leonardo",
        lambda: LeonardoAdapter(api_key=settings.LEONARDO_API_KEY),
    )
    engine_registry.register_image_engine(
        "ideogram",
        lambda: IdeogramAdapter(api_key=settings.IDEOGRAM_API_KEY),
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

    # TTS Engines
    engine_registry.register_tts_engine(
        "openai-tts", lambda: OpenAITTSAdapter(api_key=settings.OPENAI_API_KEY)
    )
    engine_registry.register_tts_engine(
        "elevenlabs", lambda: ElevenLabsTTSAdapter(api_key=settings.ELEVENLABS_API_KEY)
    )
    engine_registry.register_tts_engine("edge-tts", EdgeTTSAdapter)

    engine_registry.register_stt_engine(
        "openai-stt", lambda: OpenAISTTAdapter(api_key=settings.OPENAI_API_KEY)
    )

    engine_registry.register_bgm_engine("static-bgm", StaticBGMAdapter)
    engine_registry.register_bgm_engine(
        "lyria", lambda: LyriaAdapter(api_key=settings.GOOGLE_API_KEY)
    )
    engine_registry.register_bgm_engine(
        "elevenlabs-music",
        lambda: ElevenLabsMusicAdapter(api_key=settings.ELEVENLABS_API_KEY),
    )
    engine_registry.register_bgm_engine(
        "mubert",
        lambda: MubertAdapter(
            access_token=settings.MUBERT_ACCESS_TOKEN,
            customer_id=settings.MUBERT_CUSTOMER_ID,
        ),
    )
