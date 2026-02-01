from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
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

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    return UserSettingsResponse(
        default_llm_engine=user_settings.default_llm_engine,
        default_image_engine=user_settings.default_image_engine,
        default_video_engine=user_settings.default_video_engine,
        ollama_url=user_settings.ollama_url,
        comfyui_url=user_settings.comfyui_url,
        has_openai_key=bool(user_settings.openai_api_key),
        has_fal_key=bool(user_settings.fal_api_key),
        has_firecrawl_key=bool(user_settings.firecrawl_api_key),
    )


@router.put("/", response_model=UserSettingsResponse)
async def update_settings(
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    update_data = settings_in.model_dump(exclude_unset=True)

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

    for key, value in update_data.items():
        setattr(user_settings, key, value)

    session.add(user_settings)
    session.commit()
    session.refresh(user_settings)

    return UserSettingsResponse(
        default_llm_engine=user_settings.default_llm_engine,
        default_image_engine=user_settings.default_image_engine,
        default_video_engine=user_settings.default_video_engine,
        ollama_url=user_settings.ollama_url,
        comfyui_url=user_settings.comfyui_url,
        has_openai_key=bool(user_settings.openai_api_key),
        has_fal_key=bool(user_settings.fal_api_key),
        has_firecrawl_key=bool(user_settings.firecrawl_api_key),
    )


@router.post("/test-connection")
async def test_connection(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

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
