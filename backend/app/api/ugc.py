from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.encryption import decrypt_api_key
from app.core.registry import engine_registry
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import User, UserSettings
from app.services.video.interfaces import AvatarInfo, VoiceInfo

router = APIRouter(prefix="/ugc", tags=["ugc"])

UGC_ENGINE_TYPES = Literal["heygen", "d-id", "sadtalker"]


class UGCEngineInfo(BaseModel):
    engine: str
    name: str
    supports_ugc: bool
    requires_api_key: bool
    has_api_key: bool


class UGCEnginesResponse(BaseModel):
    engines: List[UGCEngineInfo]
    default_engine: str | None


class AvatarsResponse(BaseModel):
    avatars: List[AvatarInfo]
    engine: str


class VoicesResponse(BaseModel):
    voices: List[VoiceInfo]
    engine: str


def _get_ugc_engine_for_user(engine_name: str, user_settings: UserSettings | None):
    if engine_name == "heygen":
        api_key = None
        if user_settings and user_settings.heygen_api_key:
            api_key = decrypt_api_key(user_settings.heygen_api_key)
        if api_key:
            from app.services.video.heygen_adapter import HeyGenAdapter

            return HeyGenAdapter(api_key=api_key)
        return engine_registry.get_video_engine("heygen")

    elif engine_name == "d-id":
        api_key = None
        if user_settings and user_settings.did_api_key:
            api_key = decrypt_api_key(user_settings.did_api_key)
        if api_key:
            from app.services.video.did_adapter import DIDAdapter

            return DIDAdapter(api_key=api_key)
        return engine_registry.get_video_engine("d-id")

    elif engine_name == "sadtalker":
        return engine_registry.get_video_engine("sadtalker")

    raise HTTPException(status_code=400, detail=f"Unknown UGC engine: {engine_name}")


@router.get("/engines", response_model=UGCEnginesResponse)
@limiter.limit("60/minute")
async def list_ugc_engines(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

    engines = [
        UGCEngineInfo(
            engine="heygen",
            name="HeyGen",
            supports_ugc=True,
            requires_api_key=True,
            has_api_key=bool(user_settings and user_settings.heygen_api_key),
        ),
        UGCEngineInfo(
            engine="d-id",
            name="D-ID",
            supports_ugc=True,
            requires_api_key=True,
            has_api_key=bool(user_settings and user_settings.did_api_key),
        ),
        UGCEngineInfo(
            engine="sadtalker",
            name="SadTalker (Self-hosted)",
            supports_ugc=True,
            requires_api_key=False,
            has_api_key=True,
        ),
    ]

    default_engine = None
    if user_settings and user_settings.default_ugc_engine:
        default_engine = user_settings.default_ugc_engine
    elif user_settings and user_settings.heygen_api_key:
        default_engine = "heygen"
    elif user_settings and user_settings.did_api_key:
        default_engine = "d-id"

    return UGCEnginesResponse(engines=engines, default_engine=default_engine)


@router.get("/avatars", response_model=AvatarsResponse)
@limiter.limit("60/minute")
async def list_avatars(
    request: Request,
    engine: UGC_ENGINE_TYPES = Query(default="heygen"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

    try:
        ugc_engine = _get_ugc_engine_for_user(engine, user_settings)
        avatars = await ugc_engine.list_avatars()
        return AvatarsResponse(avatars=avatars, engine=engine)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch avatars: {str(e)}"
        )


@router.get("/voices", response_model=VoicesResponse)
@limiter.limit("60/minute")
async def list_voices(
    request: Request,
    engine: UGC_ENGINE_TYPES = Query(default="heygen"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

    try:
        ugc_engine = _get_ugc_engine_for_user(engine, user_settings)
        voices = await ugc_engine.list_voices()
        return VoicesResponse(voices=voices, engine=engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")
