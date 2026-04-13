import json
import logging
import secrets
import time
from datetime import datetime, UTC, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.encryption import decrypt_api_key, encrypt_api_key
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    Asset,
    Campaign,
    PublishConnection,
    PublishConnectionResponse,
    PublishLog,
    PublishLogResponse,
    PublishPlatformType,
    PublishRequest,
    PublishStatus,
    User,
)
from app.services.publishing.meta_adapter import MetaPublishingAdapter
from app.services.publishing.threads_adapter import ThreadsPublishingAdapter
from app.services.publishing.x_adapter import XPublishingAdapter

logger = logging.getLogger(__name__)

OAUTH_STATE_EXPIRY_SECONDS = 600
meta_oauth_state_store: dict[str, float] = {}
x_oauth_state_store: dict[str, tuple[float, str]] = {}
threads_oauth_state_store: dict[str, float] = {}

router = APIRouter(prefix="/publishing", tags=["publishing"])
meta_adapter = MetaPublishingAdapter()
x_adapter = XPublishingAdapter()
threads_adapter = ThreadsPublishingAdapter()


@router.get("/connections", response_model=List[PublishConnectionResponse])
async def list_connections(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    connections = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.is_active == True,  # noqa: E712
        )
    ).all()
    return connections


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    connection = session.exec(
        select(PublishConnection).where(
            PublishConnection.id == connection_id,
            PublishConnection.user_id == current_user.id,
        )
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    session.delete(connection)
    session.commit()
    return {"message": "Connection removed"}


@router.get("/meta/auth")
async def meta_auth(
    current_user: User = Depends(get_current_user),
):
    if not settings.FACEBOOK_APP_ID:
        raise HTTPException(status_code=400, detail="Facebook app not configured")

    state = secrets.token_urlsafe(32)
    meta_oauth_state_store[state] = time.time()
    for old_state, created_at in list(meta_oauth_state_store.items()):
        if time.time() - created_at > OAUTH_STATE_EXPIRY_SECONDS * 2:
            del meta_oauth_state_store[old_state]
    auth_url = meta_adapter.get_oauth_url(state)
    return {"auth_url": auth_url, "state": state}


@router.get("/meta/callback")
async def meta_callback(
    code: str,
    state: str = "",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if state not in meta_oauth_state_store:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing OAuth state parameter",
        )
    state_created_at = meta_oauth_state_store.pop(state)
    if time.time() - state_created_at > OAUTH_STATE_EXPIRY_SECONDS:
        raise HTTPException(
            status_code=400,
            detail="OAuth state has expired. Please try again.",
        )
    try:
        token_data = await meta_adapter.exchange_code(code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in")

    try:
        user_info = await meta_adapter.get_user_info(access_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        pages = await meta_adapter.get_pages(access_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encrypted_token = encrypt_api_key(access_token, settings.API_KEY_ENCRYPTION_KEY)
    token_expires_at = None
    if expires_in:
        token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    created_connections: list[PublishConnectionResponse] = []

    for page in pages:
        existing = session.exec(
            select(PublishConnection).where(
                PublishConnection.user_id == current_user.id,
                PublishConnection.page_id == page["id"],
                PublishConnection.platform == PublishPlatformType.FACEBOOK,
            )
        ).first()

        page_token_encrypted = encrypt_api_key(
            page["access_token"], settings.API_KEY_ENCRYPTION_KEY
        )

        if existing:
            existing.access_token = page_token_encrypted
            existing.token_expires_at = token_expires_at
            existing.account_id = user_info["id"]
            existing.account_name = user_info["name"]
            existing.page_name = page["name"]
            existing.is_active = True
            session.add(existing)
        else:
            fb_conn = PublishConnection(
                user_id=current_user.id,
                platform=PublishPlatformType.FACEBOOK,
                access_token=page_token_encrypted,
                token_expires_at=token_expires_at,
                account_id=user_info["id"],
                account_name=user_info["name"],
                page_id=page["id"],
                page_name=page["name"],
            )
            session.add(fb_conn)

        ig_account = page.get("instagram_business_account")
        if ig_account:
            ig_id = ig_account["id"]
            ig_existing = session.exec(
                select(PublishConnection).where(
                    PublishConnection.user_id == current_user.id,
                    PublishConnection.account_id == ig_id,
                    PublishConnection.platform == PublishPlatformType.INSTAGRAM,
                )
            ).first()

            if ig_existing:
                ig_existing.access_token = page_token_encrypted
                ig_existing.token_expires_at = token_expires_at
                ig_existing.page_id = page["id"]
                ig_existing.page_name = page["name"]
                ig_existing.is_active = True
                session.add(ig_existing)
            else:
                ig_conn = PublishConnection(
                    user_id=current_user.id,
                    platform=PublishPlatformType.INSTAGRAM,
                    access_token=page_token_encrypted,
                    token_expires_at=token_expires_at,
                    account_id=ig_id,
                    account_name=f"{page['name']} (Instagram)",
                    page_id=page["id"],
                    page_name=page["name"],
                )
                session.add(ig_conn)

    session.commit()

    connections = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.is_active == True,  # noqa: E712
        )
    ).all()
    created_connections = [
        PublishConnectionResponse.model_validate(c) for c in connections
    ]

    return {"connections": created_connections}


@router.get("/x/auth")
async def x_auth(
    current_user: User = Depends(get_current_user),
):
    if not settings.TWITTER_CLIENT_ID:
        raise HTTPException(status_code=400, detail="X app not configured")

    state = secrets.token_urlsafe(32)
    auth_url, code_verifier = x_adapter.get_oauth_url(state)
    x_oauth_state_store[state] = (time.time(), code_verifier)

    for old_state, (created_at, _) in list(x_oauth_state_store.items()):
        if time.time() - created_at > OAUTH_STATE_EXPIRY_SECONDS * 2:
            del x_oauth_state_store[old_state]

    return {"auth_url": auth_url, "state": state}


@router.get("/x/callback")
async def x_callback(
    code: str,
    state: str = "",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if state not in x_oauth_state_store:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing OAuth state parameter",
        )
    state_created_at, code_verifier = x_oauth_state_store.pop(state)
    if time.time() - state_created_at > OAUTH_STATE_EXPIRY_SECONDS:
        raise HTTPException(
            status_code=400,
            detail="OAuth state has expired. Please try again.",
        )

    try:
        token_data = await x_adapter.exchange_code(code, code_verifier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = token_data["access_token"]
    refresh_token_value = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    try:
        user_info = await x_adapter.get_user_info(access_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encrypted_token = encrypt_api_key(access_token, settings.API_KEY_ENCRYPTION_KEY)
    encrypted_refresh = (
        encrypt_api_key(refresh_token_value, settings.API_KEY_ENCRYPTION_KEY)
        if refresh_token_value
        else None
    )
    token_expires_at = None
    if expires_in:
        token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    existing = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.platform == PublishPlatformType.X,
        )
    ).first()

    if existing:
        existing.access_token = encrypted_token
        existing.refresh_token = encrypted_refresh
        existing.token_expires_at = token_expires_at
        existing.account_id = user_info.get("id")
        existing.account_name = user_info.get("name")
        existing.page_name = f"@{user_info.get('username', '')}"
        existing.is_active = True
        session.add(existing)
    else:
        x_conn = PublishConnection(
            user_id=current_user.id,
            platform=PublishPlatformType.X,
            access_token=encrypted_token,
            refresh_token=encrypted_refresh,
            token_expires_at=token_expires_at,
            account_id=user_info.get("id"),
            account_name=user_info.get("name"),
            page_name=f"@{user_info.get('username', '')}",
        )
        session.add(x_conn)

    session.commit()

    connections = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.is_active == True,  # noqa: E712
        )
    ).all()
    created_connections = [
        PublishConnectionResponse.model_validate(c) for c in connections
    ]
    return {"connections": created_connections}


@router.get("/threads/auth")
async def threads_auth(
    current_user: User = Depends(get_current_user),
):
    if not settings.THREADS_APP_ID:
        raise HTTPException(status_code=400, detail="Threads app not configured")

    state = secrets.token_urlsafe(32)
    threads_oauth_state_store[state] = time.time()

    for old_state, created_at in list(threads_oauth_state_store.items()):
        if time.time() - created_at > OAUTH_STATE_EXPIRY_SECONDS * 2:
            del threads_oauth_state_store[old_state]

    auth_url = threads_adapter.get_oauth_url(state)
    return {"auth_url": auth_url, "state": state}


@router.get("/threads/callback")
async def threads_callback(
    code: str,
    state: str = "",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if state not in threads_oauth_state_store:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing OAuth state parameter",
        )
    state_created_at = threads_oauth_state_store.pop(state)
    if time.time() - state_created_at > OAUTH_STATE_EXPIRY_SECONDS:
        raise HTTPException(
            status_code=400,
            detail="OAuth state has expired. Please try again.",
        )

    try:
        short_token_data = await threads_adapter.exchange_code(code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        long_token_data = await threads_adapter.exchange_long_lived_token(
            short_token_data["access_token"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = long_token_data["access_token"]
    expires_in = long_token_data.get("expires_in")

    try:
        user_info = await threads_adapter.get_user_info(access_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encrypted_token = encrypt_api_key(access_token, settings.API_KEY_ENCRYPTION_KEY)
    token_expires_at = None
    if expires_in:
        token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    existing = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.platform == PublishPlatformType.THREADS,
        )
    ).first()

    if existing:
        existing.access_token = encrypted_token
        existing.token_expires_at = token_expires_at
        existing.account_id = user_info.get("id")
        existing.account_name = user_info.get("username")
        existing.is_active = True
        session.add(existing)
    else:
        threads_conn = PublishConnection(
            user_id=current_user.id,
            platform=PublishPlatformType.THREADS,
            access_token=encrypted_token,
            token_expires_at=token_expires_at,
            account_id=user_info.get("id"),
            account_name=user_info.get("username"),
        )
        session.add(threads_conn)

    session.commit()

    connections = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.is_active == True,  # noqa: E712
        )
    ).all()
    created_connections = [
        PublishConnectionResponse.model_validate(c) for c in connections
    ]
    return {"connections": created_connections}


@router.post(
    "/campaigns/{campaign_id}/publish",
    response_model=PublishLogResponse,
)
@limiter.limit("5/minute")
async def publish_campaign(
    request: Request,
    campaign_id: int,
    publish_req: PublishRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    connection = session.exec(
        select(PublishConnection).where(
            PublishConnection.user_id == current_user.id,
            PublishConnection.platform == publish_req.platform,
            PublishConnection.is_active == True,  # noqa: E712
        )
    ).first()
    if not connection:
        raise HTTPException(
            status_code=400,
            detail=f"No active {publish_req.platform.value} connection found",
        )

    if publish_req.asset_ids:
        assets = session.exec(
            select(Asset).where(
                Asset.campaign_id == campaign_id,
                Asset.id.in_(publish_req.asset_ids),  # type: ignore[attr-defined]
            )
        ).all()
    else:
        assets = session.exec(
            select(Asset).where(Asset.campaign_id == campaign_id)
        ).all()

    if not assets:
        raise HTTPException(status_code=400, detail="No assets found to publish")

    publish_log = PublishLog(
        campaign_id=campaign_id,
        user_id=current_user.id,
        platform=publish_req.platform,
        status=PublishStatus.PUBLISHING,
        asset_ids=json.dumps([a.id for a in assets]),
        publish_metadata=json.dumps(
            {
                "caption": publish_req.caption,
                "targeting": publish_req.targeting,
                "budget": publish_req.budget,
            }
        ),
    )
    session.add(publish_log)
    session.commit()
    session.refresh(publish_log)

    page_access_token = decrypt_api_key(
        connection.access_token, settings.API_KEY_ENCRYPTION_KEY
    )

    caption = publish_req.caption or campaign.title
    image_asset = next((a for a in assets if a.type == "IMAGE"), None)
    image_url = image_asset.content if image_asset else None

    try:
        if publish_req.platform == PublishPlatformType.FACEBOOK:
            result = await meta_adapter.publish_to_facebook(
                page_access_token=page_access_token,
                page_id=connection.page_id or "",
                message=caption,
                image_url=image_url,
            )
        elif publish_req.platform == PublishPlatformType.INSTAGRAM:
            if not image_url:
                publish_log.status = PublishStatus.FAILED
                publish_log.error_message = "Instagram requires an image asset"
                session.add(publish_log)
                session.commit()
                session.refresh(publish_log)
                raise HTTPException(
                    status_code=400,
                    detail="Instagram publishing requires at least one image asset",
                )
            result = await meta_adapter.publish_to_instagram(
                page_access_token=page_access_token,
                ig_user_id=connection.account_id or "",
                image_url=image_url,
                caption=caption,
            )
        elif publish_req.platform == PublishPlatformType.X:
            result = await x_adapter.publish_tweet(
                access_token=page_access_token,
                text=caption,
            )
        elif publish_req.platform == PublishPlatformType.THREADS:
            result = await threads_adapter.publish_to_threads(
                access_token=page_access_token,
                user_id=connection.account_id or "",
                text=caption,
                image_url=image_url,
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")

        if result.get("success"):
            publish_log.status = PublishStatus.PUBLISHED
            publish_log.external_post_id = result.get("post_id")
            publish_log.external_url = result.get("post_url")
        else:
            publish_log.status = PublishStatus.FAILED
            publish_log.error_message = result.get("error", "Unknown error")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Publish failed for campaign %s", campaign_id)
        publish_log.status = PublishStatus.FAILED
        publish_log.error_message = str(e)[:500]

    session.add(publish_log)
    session.commit()
    session.refresh(publish_log)
    return publish_log


@router.get(
    "/campaigns/{campaign_id}/logs",
    response_model=List[PublishLogResponse],
)
async def get_publish_logs(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    logs = session.exec(
        select(PublishLog)
        .where(PublishLog.campaign_id == campaign_id)
        .order_by(PublishLog.created_at.desc())  # type: ignore[union-attr]
    ).all()
    return logs
