import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    Subscription,
    PlanTier,
    User,
    WhiteLabelConfig,
    WhiteLabelConfigCreate,
    WhiteLabelConfigUpdate,
    WhiteLabelConfigResponse,
    utc_now,
)

router = APIRouter(prefix="/white-label", tags=["white-label"])


def _get_subscription(session: Session, user: User) -> Subscription:
    if user.subscription:
        return user.subscription
    subscription = Subscription(user_id=user.id, tier=PlanTier.FREE)  # type: ignore[arg-type]
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def _get_config(session: Session, user: User) -> WhiteLabelConfig:
    statement = select(WhiteLabelConfig).where(WhiteLabelConfig.user_id == user.id)
    config = session.exec(statement).first()
    if not config:
        raise HTTPException(status_code=404, detail="White-label config not found")
    return config


def _sanitize_css(css: str) -> str:
    sanitized = re.sub(r"url\s*\(", "/* blocked-url */(", css, flags=re.IGNORECASE)
    sanitized = re.sub(
        r"@import", "/* blocked-import */", sanitized, flags=re.IGNORECASE
    )
    sanitized = re.sub(
        r"expression\s*\(", "/* blocked-expression */(", sanitized, flags=re.IGNORECASE
    )
    sanitized = re.sub(
        r"javascript\s*:", "/* blocked-js */", sanitized, flags=re.IGNORECASE
    )
    return sanitized


@router.get("/", response_model=WhiteLabelConfigResponse)
@limiter.limit("30/minute")
async def get_white_label(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return WhiteLabelConfigResponse.model_validate(_get_config(session, current_user))


@router.post("/", response_model=WhiteLabelConfigResponse, status_code=201)
@limiter.limit("10/minute")
async def create_white_label(
    config_in: WhiteLabelConfigCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    subscription = _get_subscription(session, current_user)
    if not subscription.limits.get("white_label"):
        raise HTTPException(
            status_code=403,
            detail="White-label requires an ULTRA plan. Please upgrade.",
        )

    existing = session.exec(
        select(WhiteLabelConfig).where(WhiteLabelConfig.user_id == current_user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="White-label config already exists")

    custom_css = (
        _sanitize_css(config_in.custom_css)
        if config_in.custom_css
        else config_in.custom_css
    )

    config = WhiteLabelConfig(
        user_id=current_user.id,  # type: ignore[arg-type]
        brand_name=config_in.brand_name,
        logo_url=config_in.logo_url,
        favicon_url=config_in.favicon_url,
        primary_color=config_in.primary_color,
        secondary_color=config_in.secondary_color,
        custom_domain=config_in.custom_domain,
        custom_css=custom_css,
        email_from_name=config_in.email_from_name,
        email_from_address=config_in.email_from_address,
        hide_powered_by=config_in.hide_powered_by,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return WhiteLabelConfigResponse.model_validate(config)


@router.put("/", response_model=WhiteLabelConfigResponse)
@limiter.limit("10/minute")
async def update_white_label(
    config_in: WhiteLabelConfigUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    config = _get_config(session, current_user)
    update_data = config_in.model_dump(exclude_unset=True)

    if "custom_css" in update_data and update_data["custom_css"]:
        update_data["custom_css"] = _sanitize_css(update_data["custom_css"])

    for key, value in update_data.items():
        setattr(config, key, value)

    config.updated_at = utc_now()
    session.add(config)
    session.commit()
    session.refresh(config)
    return WhiteLabelConfigResponse.model_validate(config)


@router.delete("/", status_code=204)
@limiter.limit("10/minute")
async def delete_white_label(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    config = _get_config(session, current_user)
    session.delete(config)
    session.commit()


@router.post("/activate", response_model=WhiteLabelConfigResponse)
@limiter.limit("10/minute")
async def activate_white_label(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    config = _get_config(session, current_user)
    config.is_active = True
    config.updated_at = utc_now()
    session.add(config)
    session.commit()
    session.refresh(config)
    return WhiteLabelConfigResponse.model_validate(config)


@router.post("/deactivate", response_model=WhiteLabelConfigResponse)
@limiter.limit("10/minute")
async def deactivate_white_label(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    config = _get_config(session, current_user)
    config.is_active = False
    config.updated_at = utc_now()
    session.add(config)
    session.commit()
    session.refresh(config)
    return WhiteLabelConfigResponse.model_validate(config)
