from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    CustomAvatar,
    CustomAvatarCreate,
    CustomAvatarResponse,
    CustomVoice,
    CustomVoiceCreate,
    CustomVoiceResponse,
    User,
    VoiceCloneStatus,
)

router = APIRouter(prefix="/custom-media", tags=["custom-media"])


@router.get("/voices", response_model=list[CustomVoiceResponse])
@limiter.limit("30/minute")
async def list_voices(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(CustomVoice).where(CustomVoice.user_id == current_user.id)
    voices = session.exec(statement).all()
    return list(voices)


@router.post("/voices", response_model=CustomVoiceResponse, status_code=201)
@limiter.limit("5/minute")
async def create_voice(
    voice_in: CustomVoiceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    voice = CustomVoice(
        user_id=current_user.id,  # type: ignore[arg-type]
        name=voice_in.name,
        language=voice_in.language,
        sample_url=voice_in.sample_url,
        provider=voice_in.provider,
        status=VoiceCloneStatus.PENDING,
    )
    session.add(voice)
    session.commit()
    session.refresh(voice)
    return voice


@router.get("/voices/{voice_id}/status", response_model=CustomVoiceResponse)
@limiter.limit("30/minute")
async def get_voice_status(
    voice_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    voice = session.get(CustomVoice, voice_id)
    if not voice or voice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.delete("/voices/{voice_id}", status_code=204)
@limiter.limit("5/minute")
async def delete_voice(
    voice_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    voice = session.get(CustomVoice, voice_id)
    if not voice or voice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Voice not found")
    session.delete(voice)
    session.commit()


@router.get("/avatars", response_model=list[CustomAvatarResponse])
@limiter.limit("30/minute")
async def list_avatars(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(CustomAvatar).where(CustomAvatar.user_id == current_user.id)
    avatars = session.exec(statement).all()
    return list(avatars)


@router.post("/avatars", response_model=CustomAvatarResponse, status_code=201)
@limiter.limit("5/minute")
async def create_avatar(
    avatar_in: CustomAvatarCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    avatar = CustomAvatar(
        user_id=current_user.id,  # type: ignore[arg-type]
        name=avatar_in.name,
        provider=avatar_in.provider,
        photo_url=avatar_in.photo_url,
        status=VoiceCloneStatus.PENDING,
    )
    session.add(avatar)
    session.commit()
    session.refresh(avatar)
    return avatar


@router.get("/avatars/{avatar_id}/status", response_model=CustomAvatarResponse)
@limiter.limit("30/minute")
async def get_avatar_status(
    avatar_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    avatar = session.get(CustomAvatar, avatar_id)
    if not avatar or avatar.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar


@router.delete("/avatars/{avatar_id}", status_code=204)
@limiter.limit("5/minute")
async def delete_avatar(
    avatar_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    avatar = session.get(CustomAvatar, avatar_id)
    if not avatar or avatar.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Avatar not found")
    session.delete(avatar)
    session.commit()
