from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import Asset, Campaign, User, UserSettings
from app.services.ai_labeling import (
    apply_ai_label,
    apply_labels_to_campaign,
    get_disclosure_metadata,
)

router = APIRouter(prefix="/ai-labeling", tags=["ai-labeling"])


@router.get("/settings")
@limiter.limit("30/minute")
async def get_ai_labeling_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_settings = session.get(UserSettings, current_user.id)

    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    return {
        "ai_disclosure_enabled": user_settings.ai_disclosure_enabled,
        "ai_label_text": user_settings.ai_label_text,
        "ai_label_position": user_settings.ai_label_position,
    }


@router.post("/assets/{asset_id}/label")
@limiter.limit("30/minute")
async def label_asset(
    request: Request,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    campaign = session.get(Campaign, asset.campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    user_settings = session.get(UserSettings, current_user.id)
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    labeled_asset = apply_ai_label(asset, user_settings, session)
    metadata = get_disclosure_metadata(labeled_asset)

    return {"asset_id": labeled_asset.id, "disclosure": metadata}


@router.post("/campaigns/{campaign_id}/label")
@limiter.limit("30/minute")
async def label_campaign_assets(
    request: Request,
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.get(Campaign, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    count = apply_labels_to_campaign(campaign_id, current_user, session)

    return {"campaign_id": campaign_id, "labeled_count": count}
