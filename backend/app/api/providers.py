"""Provider management API routes.

This module provides endpoints for managing AI provider credentials,
accessing the provider registry, and testing provider connectivity /
compatibility.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import (
    User,
    ProviderCredential,
    ProviderCredentialUpsert,
    ProviderCredentialResponse,
    ProviderCredentialTestResult,
)
from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.core.encryption import encrypt_api_key, decrypt_api_key
from app.core.credential_resolver import dual_write_credential
from app.core.config import settings
from app.core.providers import (
    list_providers,
    get_provider_manifest,
    provider_exists,
    get_shared_key_provider,
    get_shared_url_provider,
    ProviderType,
)
from app.services.usage import check_byok_access


def _self_hosted_url_placeholder(provider_name: str) -> Optional[str]:
    if provider_name == "ollama":
        return "http://localhost:11434"
    if provider_name in {"comfyui", "comfyui-video"}:
        return "http://localhost:8188"
    if provider_name == "sadtalker":
        return "http://localhost:7860"
    return None


def _build_provider_payload(provider: Any) -> dict[str, Any]:
    capabilities: list[dict[str, str]] = []
    if provider.provider_name == "comfyui":
        capabilities = [
            {
                "name": "connection",
                "description": "Stable ComfyUI server endpoints are reachable",
            },
            {
                "name": "image_workflow",
                "description": "Image workflows depend on installed nodes and mapped models",
            },
        ]
    elif provider.provider_name == "comfyui-video":
        capabilities = [
            {
                "name": "connection",
                "description": "Shares the ComfyUI endpoint with image workflows",
            },
            {
                "name": "video_workflow",
                "description": "Video workflows depend on installed nodes and mapped models",
            },
        ]
    elif provider.provider_name == "ollama":
        capabilities = [{"name": "chat", "description": "Self-hosted local LLM API"}]

    shared_credentials_note = None
    shared_credentials_with: list[str] = []
    if provider.shared_key_provider:
        shared_credentials_note = (
            f"Uses same credentials as {provider.shared_key_provider}"
        )
        shared_credentials_with = [provider.shared_key_provider]
    elif provider.shared_url_provider:
        shared_credentials_note = (
            f"Uses same endpoint as {provider.shared_url_provider}"
        )
        shared_credentials_with = [provider.shared_url_provider]

    return {
        "name": provider.provider_name,
        "display_name": provider.display_name,
        "provider_type": provider.provider_type.value,
        "capabilities": capabilities,
        "requires_key": provider.requires_key,
        "requires_url": provider.requires_url,
        "key_placeholder": None,
        "url_placeholder": _self_hosted_url_placeholder(provider.provider_name),
        "shared_credentials_note": shared_credentials_note,
        "shared_credentials_with": shared_credentials_with,
        "is_local": provider.requires_url,
        "description": provider.description,
        "documentation_url": provider.docs_url,
    }


def _result(
    provider_name: str,
    success: bool,
    message: str,
    *,
    details: Optional[dict[str, Any]] = None,
) -> ProviderCredentialTestResult:
    if details:
        message = f"{message} | details={details}"
    return ProviderCredentialTestResult(
        provider_name=provider_name,
        success=success,
        message=message,
    )


router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/registry")
@limiter.limit("60/minute")
async def get_provider_registry(
    request: Request,
    provider_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get the list of available providers from the registry.

    Optionally filter by provider type (llm, image, video, ugc, scraper).
    """
    if provider_type:
        try:
            ptype = ProviderType(provider_type.lower())
            providers = list_providers(ptype)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider_type. Must be one of: {[t.value for t in ProviderType]}",
            )
    else:
        providers = list_providers()

    return {"providers": [_build_provider_payload(p) for p in providers]}


@router.get("/credentials")
@limiter.limit("60/minute")
async def get_provider_credentials(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get all provider credentials for the current user.

    Returns credentials without the actual API keys (only indicates if they exist).
    """
    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == current_user.id
    )
    credentials = session.exec(statement).all()

    providers_by_name = {p.provider_name: p for p in list_providers()}
    return {
        "credentials": [
            {
                "provider_name": cred.provider_name,
                "display_name": providers_by_name[cred.provider_name].display_name
                if cred.provider_name in providers_by_name
                else cred.provider_name,
                "provider_type": cred.provider_type,
                "is_configured": bool(cred.credential_key) or bool(cred.endpoint_url),
                "has_key": bool(cred.credential_key),
                "has_url": bool(cred.endpoint_url),
                "last_tested_at": None,
                "last_test_success": None,
            }
            for cred in credentials
        ]
    }


@router.post("/credentials", response_model=ProviderCredentialResponse)
@limiter.limit("20/minute")
async def upsert_provider_credential(
    request: Request,
    credential_in: ProviderCredentialUpsert,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create or update a provider credential.

    If a credential for this provider already exists, it will be updated.
    The API key will be encrypted before storage.
    """
    # Validate provider exists in manifest
    if not provider_exists(credential_in.provider_name):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {credential_in.provider_name}",
        )

    manifest = get_provider_manifest(credential_in.provider_name)
    if not manifest:
        raise HTTPException(
            status_code=400,
            detail=f"Provider manifest not found: {credential_in.provider_name}",
        )

    if manifest.requires_key:
        check_byok_access(session, current_user)

    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == current_user.id,
        ProviderCredential.provider_name == credential_in.provider_name,
    )
    existing = session.exec(statement).first()

    effective_key = credential_in.credential_key or (
        existing.credential_key if existing else None
    )
    effective_url = (
        credential_in.endpoint_url
        if credential_in.endpoint_url is not None
        else (existing.endpoint_url if existing else None)
    )

    if manifest.requires_key and not effective_key:
        raise HTTPException(
            status_code=400,
            detail=f"Provider {credential_in.provider_name} requires an API key",
        )

    if manifest.requires_url and not effective_url:
        raise HTTPException(
            status_code=400,
            detail=f"Provider {credential_in.provider_name} requires an endpoint URL",
        )

    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID is missing")

    dual_write_credential(
        session,
        current_user.id,
        credential_in.provider_name,
        api_key=credential_in.credential_key,
        endpoint_url=credential_in.endpoint_url,
    )

    credential = session.exec(statement).first()
    if not credential:
        raise HTTPException(
            status_code=500, detail="Provider credential could not be created"
        )

    if credential_in.is_active is not None:
        credential.is_active = credential_in.is_active
        session.add(credential)

    session.commit()
    session.refresh(credential)

    if credential.id is None:
        raise HTTPException(status_code=500, detail="Provider credential ID is missing")

    return ProviderCredentialResponse(
        id=credential.id,
        user_id=credential.user_id,
        provider_type=credential.provider_type,
        provider_name=credential.provider_name,
        has_credential_key=bool(credential.credential_key),
        endpoint_url=credential.endpoint_url,
        is_active=credential.is_active,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )


@router.delete("/credentials/{provider_name}")
@limiter.limit("20/minute")
async def delete_provider_credential(
    request: Request,
    provider_name: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete a provider credential."""
    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == current_user.id,
        ProviderCredential.provider_name == provider_name,
    )
    credential = session.exec(statement).first()

    if not credential:
        raise HTTPException(
            status_code=404,
            detail=f"Credential for provider {provider_name} not found",
        )

    session.delete(credential)
    session.commit()

    return {"message": f"Credential for {provider_name} deleted successfully"}


@router.post(
    "/credentials/{provider_name}/test", response_model=ProviderCredentialTestResult
)
@limiter.limit("10/minute")
async def test_provider_credential(
    request: Request,
    provider_name: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Test a provider credential by making a simple API call.

    Returns success status and a message.
    """
    # Validate provider exists
    if not provider_exists(provider_name):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {provider_name}",
        )

    manifest = get_provider_manifest(provider_name)
    if not manifest:
        raise HTTPException(
            status_code=400,
            detail=f"Provider manifest not found: {provider_name}",
        )

    # Get credential from new table
    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == current_user.id,
        ProviderCredential.provider_name == provider_name,
    )
    direct_credential = session.exec(statement).first()

    # Check shared key providers (e.g., fal-video shares key with fal)
    shared_provider = get_shared_key_provider(provider_name)
    shared_key_credential = None
    if shared_provider:
        statement = select(ProviderCredential).where(
            ProviderCredential.user_id == current_user.id,
            ProviderCredential.provider_name == shared_provider,
        )
        shared_key_credential = session.exec(statement).first()

    # Check shared URL providers (e.g., comfyui-video shares URL with comfyui)
    shared_url_provider = get_shared_url_provider(provider_name)
    shared_url_credential = None
    if shared_url_provider:
        statement = select(ProviderCredential).where(
            ProviderCredential.user_id == current_user.id,
            ProviderCredential.provider_name == shared_url_provider,
        )
        shared_url_credential = session.exec(statement).first()

    credential = direct_credential or shared_key_credential or shared_url_credential

    # Fallback to legacy UserSettings
    if not credential:
        from app.models.models import UserSettings

        user_settings = session.get(UserSettings, current_user.id)  # type: ignore[arg-type]
        if user_settings:
            legacy_key_map = {
                "openai": user_settings.openai_api_key,
                "anthropic": user_settings.anthropic_api_key,
                "gemini": user_settings.google_api_key,
                "groq": user_settings.groq_api_key,
                "fal": user_settings.fal_api_key,
                "flux-pro": user_settings.fal_api_key,
                "fal-video": user_settings.fal_api_key,
                "firecrawl": user_settings.firecrawl_api_key,
                "heygen": user_settings.heygen_api_key,
                "d-id": user_settings.did_api_key,
            }
            legacy_url_map = {
                "ollama": user_settings.ollama_url,
                "comfyui": user_settings.comfyui_url,
                "comfyui-video": user_settings.comfyui_url,
                "sadtalker": user_settings.sadtalker_url,
            }

            legacy_key = legacy_key_map.get(provider_name)
            legacy_url = legacy_url_map.get(provider_name)

            if legacy_key:
                try:
                    api_key = decrypt_api_key(
                        legacy_key,
                        settings.API_KEY_ENCRYPTION_KEY,
                    )
                    return await _test_provider_api(provider_name, api_key, legacy_url)
                except Exception as e:
                    return ProviderCredentialTestResult(
                        provider_name=provider_name,
                        success=False,
                        message=f"Failed to decrypt legacy credential: {str(e)}",
                    )
            elif legacy_url and manifest.requires_url:
                return await _test_provider_api(provider_name, "", legacy_url)

    resolved_endpoint_url = None
    if direct_credential and direct_credential.endpoint_url:
        resolved_endpoint_url = direct_credential.endpoint_url
    elif shared_url_credential and shared_url_credential.endpoint_url:
        resolved_endpoint_url = shared_url_credential.endpoint_url

    if (
        manifest.requires_url
        and resolved_endpoint_url
        and not (credential and credential.credential_key)
    ):
        return await _test_provider_api(provider_name, "", resolved_endpoint_url)

    if not credential or not credential.credential_key:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=False,
            message="No credential found for this provider",
        )

    # Decrypt and test the credential
    try:
        api_key = decrypt_api_key(
            credential.credential_key,
            settings.API_KEY_ENCRYPTION_KEY,
        )
    except Exception as e:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=False,
            message=f"Failed to decrypt credential: {str(e)}",
        )

    return await _test_provider_api(provider_name, api_key, resolved_endpoint_url)


@router.post(
    "/credentials/{provider_name}/test-compatibility",
    response_model=ProviderCredentialTestResult,
)
@limiter.limit("10/minute")
async def test_provider_compatibility(
    request: Request,
    provider_name: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not provider_exists(provider_name):
        raise HTTPException(
            status_code=400, detail=f"Unknown provider: {provider_name}"
        )

    if provider_name not in {"comfyui", "comfyui-video"}:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=True,
            message="Compatibility testing is not implemented for this provider yet",
            test_type="compatibility",
            capabilities={},
        )

    statement = select(ProviderCredential).where(
        ProviderCredential.user_id == current_user.id,
        ProviderCredential.provider_name == provider_name,
    )
    credential = session.exec(statement).first()
    if not credential and provider_name == "comfyui-video":
        shared_statement = select(ProviderCredential).where(
            ProviderCredential.user_id == current_user.id,
            ProviderCredential.provider_name == "comfyui",
        )
        credential = session.exec(shared_statement).first()

    if not credential or not credential.endpoint_url:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=False,
            message="No endpoint URL found for compatibility test",
            test_type="compatibility",
        )

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{credential.endpoint_url}/object_info",
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                node_types = list(data.keys())

                capabilities = {
                    "node_types_count": len(node_types),
                    "sample_nodes": node_types[:10] if node_types else [],
                }

                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message=f"Compatibility check passed. Found {len(node_types)} node types.",
                    test_type="compatibility",
                    capabilities=capabilities,
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"ComfyUI returned status {response.status_code}",
                    test_type="compatibility",
                )
    except Exception as e:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=False,
            message=f"Compatibility test failed: {str(e)}",
            test_type="compatibility",
        )


async def _test_provider_api(
    provider_name: str, api_key: str, endpoint_url: Optional[str]
) -> ProviderCredentialTestResult:
    """Test a provider API with the given credentials."""
    manifest = get_provider_manifest(provider_name)
    if not manifest:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=False,
            message="Provider manifest not found",
        )

    try:
        if manifest.provider_type == ProviderType.LLM:
            return await _test_llm_provider(provider_name, api_key, endpoint_url)
        elif manifest.provider_type == ProviderType.IMAGE:
            return await _test_image_provider(provider_name, api_key, endpoint_url)
        elif manifest.provider_type == ProviderType.VIDEO:
            return await _test_video_provider(provider_name, api_key, endpoint_url)
        elif manifest.provider_type == ProviderType.UGC:
            return await _test_ugc_provider(provider_name, api_key, endpoint_url)
        elif manifest.provider_type == ProviderType.SCRAPER:
            return await _test_scraper_provider(provider_name, api_key, endpoint_url)
        else:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=True,
                message="Provider type does not support automated testing",
            )
    except Exception as e:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=False,
            message=f"Test failed: {str(e)}",
        )


async def _test_llm_provider(
    provider_name: str, api_key: str, endpoint_url: Optional[str]
) -> ProviderCredentialTestResult:
    """Test an LLM provider."""
    if provider_name == "openai":
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            client.models.list()
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=True,
                message="Successfully connected to OpenAI API",
            )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"OpenAI API test failed: {str(e)}",
            )
    elif provider_name == "anthropic":
        try:
            import httpx

            response = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to Anthropic API",
                )
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Anthropic API returned status {response.status_code}",
            )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Anthropic API test failed: {str(e)}",
            )
    elif provider_name == "groq":
        try:
            import httpx

            response = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to Groq API",
                )
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Groq API returned status {response.status_code}",
            )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Groq API test failed: {str(e)}",
            )
    elif provider_name == "ollama":
        if not endpoint_url:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message="Ollama requires an endpoint URL",
            )
        try:
            import httpx

            response = httpx.get(f"{endpoint_url}/api/tags", timeout=10.0)
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to Ollama server",
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"Ollama server returned status {response.status_code}",
                )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Ollama connection failed: {str(e)}",
            )
    else:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=True,
            message="LLM provider test not implemented, assuming valid",
        )


async def _test_image_provider(
    provider_name: str, api_key: str, endpoint_url: Optional[str]
) -> ProviderCredentialTestResult:
    """Test an image provider."""
    if provider_name in ("fal", "flux-pro"):
        try:
            import httpx

            response = httpx.get(
                "https://rest.alpha.fal.ai/tokens/remaining",
                headers={"Authorization": f"Key {api_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to Fal.ai API",
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"Fal.ai API returned status {response.status_code}",
                )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Fal.ai API test failed: {str(e)}",
            )
    elif provider_name == "comfyui":
        if not endpoint_url:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message="ComfyUI requires an endpoint URL",
            )
        try:
            import httpx

            response = httpx.get(f"{endpoint_url}/system_stats", timeout=10.0)
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to ComfyUI server",
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"ComfyUI server returned status {response.status_code}",
                )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"ComfyUI connection failed: {str(e)}",
            )
    else:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=True,
            message="Image provider test not implemented, assuming valid",
        )


async def _test_video_provider(
    provider_name: str, api_key: str, endpoint_url: Optional[str]
) -> ProviderCredentialTestResult:
    """Test a video provider."""
    # Fal-video uses the same API as Fal image
    if provider_name == "fal-video":
        return await _test_image_provider("fal", api_key, endpoint_url)
    elif provider_name == "comfyui-video":
        return await _test_image_provider("comfyui", api_key, endpoint_url)
    else:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=True,
            message="Video provider test not implemented, assuming valid",
        )


async def _test_ugc_provider(
    provider_name: str, api_key: str, endpoint_url: Optional[str]
) -> ProviderCredentialTestResult:
    """Test a UGC provider."""
    if provider_name == "heygen":
        try:
            import httpx

            response = httpx.get(
                "https://api.heygen.com/v2/avatars",
                headers={"X-Api-Key": api_key},
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to HeyGen API",
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"HeyGen API returned status {response.status_code}",
                )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"HeyGen API test failed: {str(e)}",
            )
    elif provider_name == "d-id":
        try:
            import httpx

            response = httpx.get(
                "https://api.d-id.com/animations",
                headers={"Authorization": f"Basic {api_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to D-ID API",
                )
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"D-ID API returned status {response.status_code}",
            )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"D-ID API test failed: {str(e)}",
            )
    elif provider_name == "sadtalker":
        if not endpoint_url:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message="SadTalker requires an endpoint URL",
            )
        try:
            import httpx

            response = httpx.get(f"{endpoint_url}/health", timeout=10.0)
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to SadTalker server",
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"SadTalker server returned status {response.status_code}",
                )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"SadTalker connection failed: {str(e)}",
            )
    else:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=True,
            message="UGC provider test not implemented, assuming valid",
        )


async def _test_scraper_provider(
    provider_name: str, api_key: str, endpoint_url: Optional[str]
) -> ProviderCredentialTestResult:
    """Test a scraper provider."""
    if provider_name == "firecrawl":
        try:
            import httpx

            response = httpx.get(
                "https://api.firecrawl.dev/v1/team/credit-usage",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=True,
                    message="Successfully connected to Firecrawl API",
                )
            else:
                return ProviderCredentialTestResult(
                    provider_name=provider_name,
                    success=False,
                    message=f"Firecrawl API returned status {response.status_code}",
                )
        except Exception as e:
            return ProviderCredentialTestResult(
                provider_name=provider_name,
                success=False,
                message=f"Firecrawl API test failed: {str(e)}",
            )
    else:
        return ProviderCredentialTestResult(
            provider_name=provider_name,
            success=True,
            message="Scraper provider test not implemented, assuming valid",
        )
