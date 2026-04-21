"""Provider manifest and registry for OpenSNS.

This module defines static metadata for all supported AI providers
and provides utilities for managing provider credentials.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProviderType(str, Enum):
    """Types of AI providers."""

    LLM = "llm"
    IMAGE = "image"
    VIDEO = "video"
    UGC = "ugc"
    SCRAPER = "scraper"
    TTS = "tts"
    STT = "stt"
    BGM = "bgm"


class ProviderRegistryItem(BaseModel):
    """Static metadata for a provider."""

    model_config = ConfigDict(frozen=True)

    provider_type: ProviderType
    provider_name: str
    display_name: str
    description: str
    requires_key: bool
    requires_url: bool
    # If True, this provider can share keys with other providers of the same type
    # e.g., Fal.ai provides both image and video services under one key
    shared_key_provider: Optional[str] = None
    # If True, this provider can share URLs with other providers of the same type
    shared_url_provider: Optional[str] = None
    # Documentation URL for the provider
    docs_url: Optional[str] = None


# Static provider manifest
# This defines all supported providers and their metadata
PROVIDER_MANIFEST: dict[str, ProviderRegistryItem] = {
    # LLM Providers
    "openai": ProviderRegistryItem(
        provider_type=ProviderType.LLM,
        provider_name="openai",
        display_name="OpenAI",
        description="GPT-4o, GPT-4, GPT-3.5 Turbo models",
        requires_key=True,
        requires_url=False,
        docs_url="https://platform.openai.com/api-keys",
    ),
    "anthropic": ProviderRegistryItem(
        provider_type=ProviderType.LLM,
        provider_name="anthropic",
        display_name="Anthropic",
        description="Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku",
        requires_key=True,
        requires_url=False,
        docs_url="https://console.anthropic.com/settings/keys",
    ),
    "gemini": ProviderRegistryItem(
        provider_type=ProviderType.LLM,
        provider_name="gemini",
        display_name="Google Gemini",
        description="Gemini 1.5 Pro, Gemini 1.5 Flash models",
        requires_key=True,
        requires_url=False,
        docs_url="https://aistudio.google.com/app/apikey",
    ),
    "groq": ProviderRegistryItem(
        provider_type=ProviderType.LLM,
        provider_name="groq",
        display_name="Groq",
        description="Ultra-fast inference for open-source models (Llama, Mixtral)",
        requires_key=True,
        requires_url=False,
        docs_url="https://console.groq.com/keys",
    ),
    "ollama": ProviderRegistryItem(
        provider_type=ProviderType.LLM,
        provider_name="ollama",
        display_name="Ollama",
        description="Self-hosted open-source LLMs (Llama, Mistral, etc.)",
        requires_key=False,
        requires_url=True,
        docs_url="https://ollama.com",
    ),
    "openrouter": ProviderRegistryItem(
        provider_type=ProviderType.LLM,
        provider_name="openrouter",
        display_name="OpenRouter",
        description="Unified API for 200+ LLM models (GPT-4o, Claude, Gemini, etc.)",
        requires_key=True,
        requires_url=False,
        docs_url="https://openrouter.ai/keys",
    ),
    # Image Providers
    "fal": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="fal",
        display_name="Fal.ai",
        description="Fast image generation with FLUX.1, Stable Diffusion",
        requires_key=True,
        requires_url=False,
        docs_url="https://fal.ai/dashboard/keys",
    ),
    "flux-pro": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="flux-pro",
        display_name="Flux Pro (via Fal.ai)",
        description="High-quality image generation with FLUX.1 [pro]",
        requires_key=True,
        requires_url=False,
        shared_key_provider="fal",
        docs_url="https://fal.ai/dashboard/keys",
    ),
    "comfyui": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="comfyui",
        display_name="ComfyUI",
        description="Self-hosted ComfyUI for custom workflows",
        requires_key=False,
        requires_url=True,
        docs_url="https://github.com/comfyanonymous/ComfyUI",
    ),
    "openrouter-image": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="openrouter-image",
        display_name="OpenRouter Image",
        description="GPT Image, Nano Banana (Gemini Flash Image) via OpenRouter",
        requires_key=True,
        requires_url=False,
        shared_key_provider="openrouter",
        docs_url="https://openrouter.ai/docs",
    ),
    "openai-image": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="openai-image",
        display_name="OpenAI GPT Image",
        description="GPT Image 1/1.5, DALL-E 3 image generation",
        requires_key=True,
        requires_url=False,
        shared_key_provider="openai",
        docs_url="https://platform.openai.com/docs/guides/images",
    ),
    "replicate": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="replicate",
        display_name="Replicate",
        description="FLUX, Stable Diffusion and 1000+ community models",
        requires_key=True,
        requires_url=False,
        docs_url="https://replicate.com/account/api-tokens",
    ),
    "together": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="together",
        display_name="Together AI",
        description="FLUX.1 Schnell/Pro image generation",
        requires_key=True,
        requires_url=False,
        docs_url="https://api.together.xyz/settings/api-keys",
    ),
    "stability": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="stability",
        display_name="Stability AI",
        description="Stable Diffusion 3, Stable Image generation",
        requires_key=True,
        requires_url=False,
        docs_url="https://platform.stability.ai/account/keys",
    ),
    "bfl": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="bfl",
        display_name="Black Forest Labs",
        description="FLUX Pro/Dev directly from the creators",
        requires_key=True,
        requires_url=False,
        docs_url="https://api.bfl.ai",
    ),
    "leonardo": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="leonardo",
        display_name="Leonardo AI",
        description="High-quality product and creative image generation",
        requires_key=True,
        requires_url=False,
        docs_url="https://app.leonardo.ai/api-access",
    ),
    "ideogram": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="ideogram",
        display_name="Ideogram",
        description="Text rendering and creative image generation",
        requires_key=True,
        requires_url=False,
        docs_url="https://ideogram.ai/manage-api",
    ),
    "gemini-image": ProviderRegistryItem(
        provider_type=ProviderType.IMAGE,
        provider_name="gemini-image",
        display_name="Google Imagen 4",
        description="Photorealistic image generation via Imagen 4",
        requires_key=True,
        requires_url=False,
        shared_key_provider="gemini",
        docs_url="https://ai.google.dev/gemini-api/docs/imagen",
    ),
    # Video Providers
    "fal-video": ProviderRegistryItem(
        provider_type=ProviderType.VIDEO,
        provider_name="fal-video",
        display_name="Fal.ai Video",
        description="Fast video generation with various models",
        requires_key=True,
        requires_url=False,
        shared_key_provider="fal",
        docs_url="https://fal.ai/dashboard/keys",
    ),
    "runway": ProviderRegistryItem(
        provider_type=ProviderType.VIDEO,
        provider_name="runway",
        display_name="Runway",
        description="Gen-3 Alpha video generation",
        requires_key=True,
        requires_url=False,
        docs_url="https://runwayml.com",
    ),
    "comfyui-video": ProviderRegistryItem(
        provider_type=ProviderType.VIDEO,
        provider_name="comfyui-video",
        display_name="ComfyUI Video",
        description="Self-hosted ComfyUI for video workflows",
        requires_key=False,
        requires_url=True,
        shared_url_provider="comfyui",
        docs_url="https://github.com/comfyanonymous/ComfyUI",
    ),
    "gemini-video": ProviderRegistryItem(
        provider_type=ProviderType.VIDEO,
        provider_name="gemini-video",
        display_name="Google Veo 3",
        description="AI video generation via Veo 3 (8s clips)",
        requires_key=True,
        requires_url=False,
        shared_key_provider="gemini",
        docs_url="https://ai.google.dev/gemini-api/docs/video",
    ),
    # UGC Video Providers
    "heygen": ProviderRegistryItem(
        provider_type=ProviderType.UGC,
        provider_name="heygen",
        display_name="HeyGen",
        description="AI avatar videos with 100+ avatars and voices",
        requires_key=True,
        requires_url=False,
        docs_url="https://app.heygen.com/settings?nav=API",
    ),
    "d-id": ProviderRegistryItem(
        provider_type=ProviderType.UGC,
        provider_name="d-id",
        display_name="D-ID",
        description="AI avatar videos with photo-realistic results",
        requires_key=True,
        requires_url=False,
        docs_url="https://studio.d-id.com/account-settings",
    ),
    "sadtalker": ProviderRegistryItem(
        provider_type=ProviderType.UGC,
        provider_name="sadtalker",
        display_name="SadTalker",
        description="Self-hosted open-source talking head generation",
        requires_key=False,
        requires_url=True,
        docs_url="https://github.com/OpenTalker/SadTalker",
    ),
    # Scraper Providers
    "firecrawl": ProviderRegistryItem(
        provider_type=ProviderType.SCRAPER,
        provider_name="firecrawl",
        display_name="Firecrawl",
        description="Website scraping and content extraction",
        requires_key=True,
        requires_url=False,
        docs_url="https://www.firecrawl.dev/account",
    ),
    # TTS Providers
    "openai-tts": ProviderRegistryItem(
        provider_type=ProviderType.TTS,
        provider_name="openai-tts",
        display_name="OpenAI TTS",
        description="High-quality text-to-speech with gpt-4o-mini-tts",
        requires_key=True,
        requires_url=False,
        shared_key_provider="openai",
        docs_url="https://platform.openai.com/docs/guides/text-to-speech",
    ),
    "elevenlabs": ProviderRegistryItem(
        provider_type=ProviderType.TTS,
        provider_name="elevenlabs",
        display_name="ElevenLabs",
        description="Premium text-to-speech with voice cloning",
        requires_key=True,
        requires_url=False,
        docs_url="https://elevenlabs.io/docs/api-reference/getting-started",
    ),
    "edge-tts": ProviderRegistryItem(
        provider_type=ProviderType.TTS,
        provider_name="edge-tts",
        display_name="Edge TTS",
        description="Free text-to-speech via Microsoft Edge (no API key required)",
        requires_key=False,
        requires_url=False,
    ),
    "gemini-tts": ProviderRegistryItem(
        provider_type=ProviderType.TTS,
        provider_name="gemini-tts",
        display_name="Google Gemini TTS",
        description="High-quality text-to-speech with 30 voices via Gemini API",
        requires_key=True,
        requires_url=False,
        shared_key_provider="gemini",
        docs_url="https://ai.google.dev/gemini-api/docs/speech-generation",
    ),
    # STT Providers
    "openai-stt": ProviderRegistryItem(
        provider_type=ProviderType.STT,
        provider_name="openai-stt",
        display_name="OpenAI Whisper",
        description="Speech-to-text transcription via Whisper model",
        requires_key=True,
        requires_url=False,
        shared_key_provider="openai",
        docs_url="https://platform.openai.com/docs/guides/speech-to-text",
    ),
    "gemini-stt": ProviderRegistryItem(
        provider_type=ProviderType.STT,
        provider_name="gemini-stt",
        display_name="Google Gemini STT",
        description="Speech-to-text transcription via Gemini audio understanding",
        requires_key=True,
        requires_url=False,
        shared_key_provider="gemini",
        docs_url="https://ai.google.dev/gemini-api/docs/audio",
    ),
    # BGM Providers
    "static-bgm": ProviderRegistryItem(
        provider_type=ProviderType.BGM,
        provider_name="static-bgm",
        display_name="Built-in BGM Library",
        description="Bundled royalty-free background music tracks",
        requires_key=False,
        requires_url=False,
    ),
    "lyria": ProviderRegistryItem(
        provider_type=ProviderType.BGM,
        provider_name="lyria",
        display_name="Google Lyria",
        description="AI music generation via Gemini API (Lyria 3)",
        requires_key=True,
        requires_url=False,
        shared_key_provider="gemini",
        docs_url="https://ai.google.dev/gemini-api/docs/music-generation",
    ),
    "elevenlabs-music": ProviderRegistryItem(
        provider_type=ProviderType.BGM,
        provider_name="elevenlabs-music",
        display_name="ElevenLabs Music",
        description="AI music generation with ElevenLabs",
        requires_key=True,
        requires_url=False,
        shared_key_provider="elevenlabs",
        docs_url="https://elevenlabs.io/docs/api-reference/music",
    ),
    "mubert": ProviderRegistryItem(
        provider_type=ProviderType.BGM,
        provider_name="mubert",
        display_name="Mubert",
        description="AI-generated royalty-free background music",
        requires_key=True,
        requires_url=False,
        docs_url="https://docs.mubert.com",
    ),
}


def get_provider_manifest(provider_name: str) -> Optional[ProviderRegistryItem]:
    """Get the manifest for a specific provider."""
    return PROVIDER_MANIFEST.get(provider_name)


def list_providers(
    provider_type: Optional[ProviderType] = None,
) -> list[ProviderRegistryItem]:
    """List all providers, optionally filtered by type."""
    providers = list(PROVIDER_MANIFEST.values())
    if provider_type:
        providers = [p for p in providers if p.provider_type == provider_type]
    return providers


def get_default_provider(provider_type: ProviderType) -> Optional[str]:
    """Get the default provider name for a given type."""
    defaults = {
        ProviderType.LLM: "gemini",
        ProviderType.IMAGE: "gemini-image",
        ProviderType.VIDEO: "gemini-video",
        ProviderType.UGC: None,
        ProviderType.SCRAPER: "firecrawl",
        ProviderType.TTS: "gemini-tts",
        ProviderType.STT: "gemini-stt",
        ProviderType.BGM: "lyria",
    }
    return defaults.get(provider_type)


def get_provider_type(provider_name: str) -> Optional[ProviderType]:
    """Get the type of a provider by name."""
    manifest = get_provider_manifest(provider_name)
    return manifest.provider_type if manifest else None


def provider_exists(provider_name: str) -> bool:
    """Check if a provider exists in the manifest."""
    return provider_name in PROVIDER_MANIFEST


def get_shared_key_provider(provider_name: str) -> Optional[str]:
    """Get the provider that shares keys with this provider, if any."""
    manifest = get_provider_manifest(provider_name)
    if manifest and manifest.shared_key_provider:
        return manifest.shared_key_provider
    return None


def get_shared_url_provider(provider_name: str) -> Optional[str]:
    """Get the provider that shares URLs with this provider, if any."""
    manifest = get_provider_manifest(provider_name)
    if manifest and manifest.shared_url_provider:
        return manifest.shared_url_provider
    return None
