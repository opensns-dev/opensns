"""Credential resolution helper for backward compatibility.

This module provides utilities to resolve credentials from the new
ProviderCredential table first, falling back to legacy UserSettings fields.
It also supports dual-write operations to keep both systems in sync.

TODO: After full migration to ProviderCredential table, this module can be
simplified to only read from the new table.
"""

import logging
from typing import Optional
from sqlmodel import Session, select

from app.models.models import ProviderCredential, UserSettings
from app.core.encryption import decrypt_api_key, encrypt_api_key
from app.core.config import settings
from app.core.providers import (
    get_provider_manifest,
    get_shared_key_provider,
    provider_exists,
)

logger = logging.getLogger(__name__)


# Mapping of provider names to legacy UserSettings field names
LEGACY_KEY_FIELDS = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "gemini": "google_api_key",
    "groq": "groq_api_key",
    "fal": "fal_api_key",
    "flux-pro": "fal_api_key",  # Shares key with fal
    "fal-video": "fal_api_key",  # Shares key with fal
    "firecrawl": "firecrawl_api_key",
    "heygen": "heygen_api_key",
    "d-id": "did_api_key",
    "openai-tts": "openai_api_key",  # Shares key with openai
    "elevenlabs": "elevenlabs_api_key",
}

LEGACY_URL_FIELDS = {
    "ollama": "ollama_url",
    "comfyui": "comfyui_url",
    "comfyui-video": "comfyui_url",  # Shares URL with comfyui
    "sadtalker": "sadtalker_url",
}


def resolve_credential(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve credentials for a provider, preferring new table over legacy.

    Args:
        session: Database session
        user_id: User ID
        provider_name: Provider name (e.g., "openai", "fal", "heygen")

    Returns:
        Tuple of (api_key, endpoint_url). Either may be None.
    """
    if not provider_exists(provider_name):
        logger.warning(f"Unknown provider: {provider_name}")
        return None, None

    # First, try to get from new ProviderCredential table
    api_key, endpoint_url = _get_from_provider_credential(
        session, user_id, provider_name
    )

    if api_key or endpoint_url:
        logger.debug(
            f"Resolved credentials for {provider_name} from ProviderCredential table"
        )
        return api_key, endpoint_url

    # Fallback to legacy UserSettings
    api_key, endpoint_url = _get_from_legacy_settings(session, user_id, provider_name)

    if api_key or endpoint_url:
        logger.debug(
            f"Resolved credentials for {provider_name} from legacy UserSettings"
        )

    return api_key, endpoint_url


def _get_from_provider_credential(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials from the new ProviderCredential table."""
    # Check for direct credential
    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == user_id,
        ProviderCredential.provider_name == provider_name,
        ProviderCredential.is_active == True,
    )
    credential = session.exec(statement).first()

    # If not found, check for shared key provider
    if not credential:
        shared_provider = get_shared_key_provider(provider_name)
        if shared_provider:
            statement = select(ProviderCredential).where(
                ProviderCredential.user_id == user_id,
                ProviderCredential.provider_name == shared_provider,
                ProviderCredential.is_active == True,
            )
            credential = session.exec(statement).first()

    if not credential:
        return None, None

    # Decrypt API key if present
    api_key = None
    if credential.credential_key:
        try:
            api_key = decrypt_api_key(
                credential.credential_key,
                settings.API_KEY_ENCRYPTION_KEY,
            )
        except Exception as e:
            logger.warning(f"Failed to decrypt credential for {provider_name}: {e}")
            api_key = None

    return api_key, credential.endpoint_url


def _get_from_legacy_settings(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials from legacy UserSettings fields."""
    user_settings = session.get(UserSettings, user_id)
    if not user_settings:
        return None, None

    api_key = None
    endpoint_url = None

    # Get API key from legacy field
    legacy_key_field = LEGACY_KEY_FIELDS.get(provider_name)
    if legacy_key_field:
        encrypted_key = getattr(user_settings, legacy_key_field, None)
        if encrypted_key:
            try:
                api_key = decrypt_api_key(
                    encrypted_key,
                    settings.API_KEY_ENCRYPTION_KEY,
                )
            except Exception as e:
                logger.warning(f"Failed to decrypt legacy key for {provider_name}: {e}")
                api_key = None

    # Get endpoint URL from legacy field
    legacy_url_field = LEGACY_URL_FIELDS.get(provider_name)
    if legacy_url_field:
        endpoint_url = getattr(user_settings, legacy_url_field, None)

    return api_key, endpoint_url


def dual_write_credential(
    session: Session,
    user_id: int,
    provider_name: str,
    api_key: Optional[str] = None,
    endpoint_url: Optional[str] = None,
) -> None:
    """Write credentials to both new ProviderCredential table and legacy UserSettings.

    This is used when updating settings via the legacy API to keep both systems in sync.
    The new table is considered the source of truth for reads.

    Args:
        session: Database session
        user_id: User ID
        provider_name: Provider name
        api_key: Raw API key (will be encrypted)
        endpoint_url: Endpoint URL for self-hosted providers
    """
    if not provider_exists(provider_name):
        logger.warning(f"Cannot dual-write unknown provider: {provider_name}")
        return

    manifest = get_provider_manifest(provider_name)
    if not manifest:
        return

    # Write to new ProviderCredential table
    _write_to_provider_credential(
        session,
        user_id,
        provider_name,
        manifest.provider_type.value,
        api_key,
        endpoint_url,
    )

    # Also write to legacy UserSettings for backward compatibility
    _write_to_legacy_settings(session, user_id, provider_name, api_key, endpoint_url)


def _write_to_provider_credential(
    session: Session,
    user_id: int,
    provider_name: str,
    provider_type: str,
    api_key: Optional[str],
    endpoint_url: Optional[str],
) -> None:
    """Write credential to the new ProviderCredential table."""
    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == user_id,
        ProviderCredential.provider_name == provider_name,
    )
    credential = session.exec(statement).first()

    from app.models.models import utc_now

    if credential:
        # Update existing
        if api_key:
            credential.credential_key = encrypt_api_key(
                api_key,
                settings.API_KEY_ENCRYPTION_KEY,
            )
        if endpoint_url is not None:
            credential.endpoint_url = endpoint_url
        credential.updated_at = utc_now()
    else:
        # Create new
        encrypted_key = None
        if api_key:
            encrypted_key = encrypt_api_key(
                api_key,
                settings.API_KEY_ENCRYPTION_KEY,
            )
        credential = ProviderCredential(
            user_id=user_id,
            provider_type=provider_type,
            provider_name=provider_name,
            credential_key=encrypted_key,
            endpoint_url=endpoint_url,
            is_active=True,
        )

    session.add(credential)
    # Note: Caller must commit the session


def _write_to_legacy_settings(
    session: Session,
    user_id: int,
    provider_name: str,
    api_key: Optional[str],
    endpoint_url: Optional[str],
) -> None:
    """Write credential to legacy UserSettings fields."""
    user_settings = session.get(UserSettings, user_id)
    if not user_settings:
        user_settings = UserSettings(user_id=user_id)
        session.add(user_settings)
        session.flush()  # Get the ID assigned

    # Write API key to legacy field
    legacy_key_field = LEGACY_KEY_FIELDS.get(provider_name)
    if legacy_key_field and api_key:
        encrypted_key = encrypt_api_key(
            api_key,
            settings.API_KEY_ENCRYPTION_KEY,
        )
        setattr(user_settings, legacy_key_field, encrypted_key)

    # Write endpoint URL to legacy field
    legacy_url_field = LEGACY_URL_FIELDS.get(provider_name)
    if legacy_url_field and endpoint_url is not None:
        setattr(user_settings, legacy_url_field, endpoint_url)

    from app.models.models import utc_now

    user_settings.updated_at = utc_now()
    session.add(user_settings)
    # Note: Caller must commit the session


def has_credential(
    session: Session,
    user_id: int,
    provider_name: str,
) -> bool:
    """Check if a user has credentials for a provider.

    Checks both the new ProviderCredential table and legacy UserSettings.
    """
    api_key, endpoint_url = resolve_credential(session, user_id, provider_name)
    return bool(api_key) or bool(endpoint_url)


def get_llm_credentials(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials for an LLM provider.

    Returns the API key and optional endpoint URL (for Ollama).
    """
    return resolve_credential(session, user_id, provider_name)


def get_image_credentials(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials for an image provider.

    Returns the API key and optional endpoint URL (for ComfyUI).
    """
    return resolve_credential(session, user_id, provider_name)


def get_video_credentials(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials for a video provider.

    Returns the API key and optional endpoint URL (for ComfyUI Video).
    """
    return resolve_credential(session, user_id, provider_name)


def get_ugc_credentials(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials for a UGC provider.

    Returns the API key and optional endpoint URL (for SadTalker).
    """
    return resolve_credential(session, user_id, provider_name)


def get_scraper_credentials(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials for a scraper provider.

    Returns the API key.
    """
    return resolve_credential(session, user_id, provider_name)


def get_tts_credentials(
    session: Session,
    user_id: int,
    provider_name: str,
) -> tuple[Optional[str], Optional[str]]:
    """Get credentials for a TTS provider."""
    return resolve_credential(session, user_id, provider_name)
