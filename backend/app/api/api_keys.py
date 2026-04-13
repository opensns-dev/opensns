from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    ApiKey,
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    User,
    utc_now,
)
from app.services.api_keys import generate_api_key, hash_api_key
from app.services.usage import get_or_create_subscription

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("/", response_model=list[ApiKeyResponse])
@limiter.limit("60/minute")
async def list_api_keys(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = (
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())  # type: ignore[union-attr]
    )
    keys = session.exec(statement).all()
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.post("/", response_model=ApiKeyCreatedResponse, status_code=201)
@limiter.limit("10/minute")
async def create_api_key(
    key_in: ApiKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    subscription = get_or_create_subscription(session, current_user)
    if not subscription.limits.get("api_access"):
        raise HTTPException(
            status_code=403,
            detail="API access requires a PRO or ULTRA plan. Please upgrade.",
        )

    raw_key = generate_api_key()
    now = utc_now()

    expires_at = None
    if key_in.expires_in_days is not None:
        expires_at = now + timedelta(days=key_in.expires_in_days)

    api_key = ApiKey(
        user_id=current_user.id,  # type: ignore[arg-type]
        name=key_in.name,
        key_prefix=raw_key[:8],
        key_hash=hash_api_key(raw_key),
        scopes=key_in.scopes or "read,write",
        expires_at=expires_at,
        created_at=now,
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,  # type: ignore[arg-type]
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.put("/{key_id}", response_model=ApiKeyResponse)
@limiter.limit("20/minute")
async def update_api_key(
    key_id: int,
    key_in: ApiKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    api_key = session.get(ApiKey, key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.name = key_in.name
    if key_in.scopes is not None:
        api_key.scopes = key_in.scopes
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return ApiKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=204)
@limiter.limit("10/minute")
async def revoke_api_key(
    key_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    api_key = session.get(ApiKey, key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    session.add(api_key)
    session.commit()
