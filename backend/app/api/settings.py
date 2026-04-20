from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from urllib.parse import urlparse
import ipaddress
from app.db import get_session
from app.models.models import (
    User,
    UserSettings,
    UserSettingsUpdate,
    UserSettingsResponse,
)
from app.core.auth import get_current_user
from app.core.encryption import encrypt_api_key, decrypt_api_key
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.credential_resolver import dual_write_credential
from app.services.usage import check_byok_access, get_or_create_subscription

API_KEY_FIELDS = {
    "openai_api_key",
    "fal_api_key",
    "firecrawl_api_key",
    "heygen_api_key",
    "did_api_key",
    "anthropic_api_key",
    "google_api_key",
    "groq_api_key",
}

# Map of legacy settings fields to provider names for dual-write
LEGACY_KEY_TO_PROVIDER = {
    "openai_api_key": "openai",
    "fal_api_key": "fal",
    "firecrawl_api_key": "firecrawl",
    "heygen_api_key": "heygen",
    "did_api_key": "d-id",
    "anthropic_api_key": "anthropic",
    "google_api_key": "gemini",
    "groq_api_key": "groq",
}

LEGACY_URL_TO_PROVIDER = {
    "ollama_url": "ollama",
    "comfyui_url": "comfyui",
    "sadtalker_url": "sadtalker",
}

router = APIRouter(prefix="/settings", tags=["settings"])


def _validate_public_url(url: str) -> None:
    """Validate that a URL is a public (non-private) address.

    Use this for external/cloud providers that should not use internal addresses.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL must use http or https scheme")
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: no hostname")
    try:
        addr = ipaddress.ip_address(hostname)
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
        ):
            raise HTTPException(
                status_code=400,
                detail="URL must not point to private or internal addresses",
            )
    except ValueError:
        pass


def _validate_engine_url(url: str) -> None:
    """Validate URL format for self-hosted engines.

    Self-hosted engines (Ollama, ComfyUI, SadTalker) are allowed to use
    localhost, private IPs, and internal addresses since they run on the
    user's own infrastructure.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL must use http or https scheme")
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: no hostname")


@router.get("/", response_model=UserSettingsResponse)
@limiter.limit("60/minute")
async def get_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)  # type: ignore[arg-type]
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    return UserSettingsResponse(
        default_llm_engine=user_settings.default_llm_engine,
        default_image_engine=user_settings.default_image_engine,
        default_video_engine=user_settings.default_video_engine,
        default_ugc_engine=user_settings.default_ugc_engine,
        ugc_enabled=user_settings.ugc_enabled,
        ugc_avatar_id=user_settings.ugc_avatar_id,
        ugc_voice_id=user_settings.ugc_voice_id,
        ollama_url=user_settings.ollama_url,
        comfyui_url=user_settings.comfyui_url,
        sadtalker_url=user_settings.sadtalker_url,
        default_tts_engine=user_settings.default_tts_engine,
        default_bgm_engine=user_settings.default_bgm_engine,
        default_stt_engine=user_settings.default_stt_engine,
        tts_enabled=user_settings.tts_enabled,
        bgm_enabled=user_settings.bgm_enabled,
        tts_voice_id=user_settings.tts_voice_id,
        bgm_style=user_settings.bgm_style,
        has_openai_key=bool(user_settings.openai_api_key),
        has_fal_key=bool(user_settings.fal_api_key),
        has_firecrawl_key=bool(user_settings.firecrawl_api_key),
        has_heygen_key=bool(user_settings.heygen_api_key),
        has_did_key=bool(user_settings.did_api_key),
        has_anthropic_key=bool(user_settings.anthropic_api_key),
        has_google_key=bool(user_settings.google_api_key),
        has_groq_key=bool(user_settings.groq_api_key),
        ai_disclosure_enabled=user_settings.ai_disclosure_enabled,
        ai_label_text=user_settings.ai_label_text,
        ai_label_position=user_settings.ai_label_position,
    )


@router.put("/", response_model=UserSettingsResponse)
@limiter.limit("20/minute")
async def update_settings(
    request: Request,
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)  # type: ignore[arg-type]
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    update_data = settings_in.model_dump(exclude_unset=True)

    has_api_key_update = any(update_data.get(f) for f in API_KEY_FIELDS)
    if has_api_key_update:
        check_byok_access(session, current_user)

    if "ollama_url" in update_data and update_data["ollama_url"]:
        _validate_engine_url(update_data["ollama_url"])
    if "comfyui_url" in update_data and update_data["comfyui_url"]:
        _validate_engine_url(update_data["comfyui_url"])
    if "sadtalker_url" in update_data and update_data["sadtalker_url"]:
        _validate_engine_url(update_data["sadtalker_url"])

    if "openai_api_key" in update_data and update_data["openai_api_key"]:
        update_data["openai_api_key"] = encrypt_api_key(
            update_data["openai_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "fal_api_key" in update_data and update_data["fal_api_key"]:
        update_data["fal_api_key"] = encrypt_api_key(
            update_data["fal_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "firecrawl_api_key" in update_data and update_data["firecrawl_api_key"]:
        update_data["firecrawl_api_key"] = encrypt_api_key(
            update_data["firecrawl_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "heygen_api_key" in update_data and update_data["heygen_api_key"]:
        update_data["heygen_api_key"] = encrypt_api_key(
            update_data["heygen_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "did_api_key" in update_data and update_data["did_api_key"]:
        update_data["did_api_key"] = encrypt_api_key(
            update_data["did_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "anthropic_api_key" in update_data and update_data["anthropic_api_key"]:
        update_data["anthropic_api_key"] = encrypt_api_key(
            update_data["anthropic_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "google_api_key" in update_data and update_data["google_api_key"]:
        update_data["google_api_key"] = encrypt_api_key(
            update_data["google_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    if "groq_api_key" in update_data and update_data["groq_api_key"]:
        update_data["groq_api_key"] = encrypt_api_key(
            update_data["groq_api_key"],
            settings.API_KEY_ENCRYPTION_KEY,
        )

    # Dual-write API keys to ProviderCredential table
    for legacy_field, provider_name in LEGACY_KEY_TO_PROVIDER.items():
        if legacy_field in update_data and update_data[legacy_field]:
            raw_key = settings_in.model_dump().get(legacy_field)
            if raw_key:
                dual_write_credential(
                    session,
                    current_user.id,  # type: ignore[arg-type]
                    provider_name,
                    api_key=raw_key,
                    endpoint_url=None,
                )

    # Dual-write endpoint URLs to ProviderCredential table
    for legacy_field, provider_name in LEGACY_URL_TO_PROVIDER.items():
        if legacy_field in update_data:
            url_value = update_data[legacy_field]
            dual_write_credential(
                session,
                current_user.id,  # type: ignore[arg-type]
                provider_name,
                api_key=None,
                endpoint_url=url_value,
            )

    for key, value in update_data.items():
        setattr(user_settings, key, value)

    session.add(user_settings)
    session.commit()
    session.refresh(user_settings)

    return UserSettingsResponse(
        default_llm_engine=user_settings.default_llm_engine,
        default_image_engine=user_settings.default_image_engine,
        default_video_engine=user_settings.default_video_engine,
        default_ugc_engine=user_settings.default_ugc_engine,
        ugc_enabled=user_settings.ugc_enabled,
        ugc_avatar_id=user_settings.ugc_avatar_id,
        ugc_voice_id=user_settings.ugc_voice_id,
        ollama_url=user_settings.ollama_url,
        comfyui_url=user_settings.comfyui_url,
        sadtalker_url=user_settings.sadtalker_url,
        default_tts_engine=user_settings.default_tts_engine,
        default_bgm_engine=user_settings.default_bgm_engine,
        default_stt_engine=user_settings.default_stt_engine,
        tts_enabled=user_settings.tts_enabled,
        bgm_enabled=user_settings.bgm_enabled,
        tts_voice_id=user_settings.tts_voice_id,
        bgm_style=user_settings.bgm_style,
        has_openai_key=bool(user_settings.openai_api_key),
        has_fal_key=bool(user_settings.fal_api_key),
        has_firecrawl_key=bool(user_settings.firecrawl_api_key),
        has_heygen_key=bool(user_settings.heygen_api_key),
        has_did_key=bool(user_settings.did_api_key),
        has_anthropic_key=bool(user_settings.anthropic_api_key),
        has_google_key=bool(user_settings.google_api_key),
        has_groq_key=bool(user_settings.groq_api_key),
        ai_disclosure_enabled=user_settings.ai_disclosure_enabled,
        ai_label_text=user_settings.ai_label_text,
        ai_label_position=user_settings.ai_label_position,
    )


@router.post("/test-connection")
@limiter.limit("20/minute")
async def test_connection(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    if not user_settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    results = {"openai": False, "fal": False}

    if user_settings.openai_api_key:
        try:
            from openai import OpenAI

            api_key = decrypt_api_key(
                user_settings.openai_api_key,
                settings.API_KEY_ENCRYPTION_KEY,
            )
            client = OpenAI(api_key=api_key)
            client.models.list()
            results["openai"] = True
        except Exception:
            results["openai"] = False

    if user_settings.fal_api_key:
        try:
            results["fal"] = True
        except Exception:
            results["fal"] = False

    return results
