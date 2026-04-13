import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import (
    AdVariant,
    AdVariantCreate,
    AdVariantResponse,
    Asset,
    AssetType,
    Campaign,
    User,
)
from app.core.auth import get_current_user
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns/{campaign_id}/variants", tags=["variants"])

VARIANT_LABELS = ["A", "B", "C", "D", "E"]


def _get_campaign_or_404(session: Session, campaign_id: int, user_id: int) -> Campaign:
    campaign = session.exec(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def _variant_to_response(variant: AdVariant) -> AdVariantResponse:
    try:
        metadata = json.loads(variant.variant_metadata)
    except (json.JSONDecodeError, TypeError):
        metadata = {}
    return AdVariantResponse(
        id=variant.id,
        campaign_id=variant.campaign_id,
        name=variant.name,
        variant_label=variant.variant_label,
        copy_headline=variant.copy_headline,
        copy_body=variant.copy_body,
        copy_cta=variant.copy_cta,
        image_asset_id=variant.image_asset_id,
        platform=variant.platform,
        is_control=variant.is_control,
        variant_metadata=metadata,
        created_at=variant.created_at,
    )


@router.get("/", response_model=List[AdVariantResponse])
async def list_variants(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    variants = session.exec(
        select(AdVariant).where(AdVariant.campaign_id == campaign_id)
    ).all()
    return [_variant_to_response(v) for v in variants]


@router.post("/", response_model=AdVariantResponse)
async def create_variant(
    campaign_id: int,
    variant_in: AdVariantCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    variant = AdVariant(
        campaign_id=campaign_id,
        **variant_in.model_dump(),
    )
    session.add(variant)
    session.commit()
    session.refresh(variant)
    return _variant_to_response(variant)


@router.post("/auto-generate", response_model=List[AdVariantResponse])
@limiter.limit("5/minute")
async def auto_generate_variants(
    request: Request,
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)

    copy_assets = session.exec(
        select(Asset).where(
            Asset.campaign_id == campaign_id, Asset.type == AssetType.COPY
        )
    ).all()

    image_assets = session.exec(
        select(Asset).where(
            Asset.campaign_id == campaign_id, Asset.type == AssetType.IMAGE
        )
    ).all()

    if not copy_assets:
        raise HTTPException(
            status_code=400,
            detail="No copy assets found for this campaign. Generate copies first.",
        )

    copies = []
    for asset in copy_assets:
        try:
            meta = json.loads(asset.asset_metadata or "{}")
        except (json.JSONDecodeError, TypeError):
            meta = {}
        copies.append(
            {
                "headline": meta.get("headline", ""),
                "body": asset.content,
                "cta": meta.get("cta", ""),
                "platform": meta.get("platform", ""),
            }
        )

    num_variants = min(len(copies), 5)
    num_variants = max(num_variants, 2)
    num_variants = min(num_variants, len(copies))

    created = []
    for i in range(num_variants):
        copy_data = copies[i % len(copies)]
        image_id = image_assets[i % len(image_assets)].id if image_assets else None
        variant = AdVariant(
            campaign_id=campaign_id,
            name=f"Variant {VARIANT_LABELS[i]}",
            variant_label=VARIANT_LABELS[i],
            copy_headline=copy_data["headline"] or None,
            copy_body=copy_data["body"] or None,
            copy_cta=copy_data["cta"] or None,
            image_asset_id=image_id,
            platform=copy_data["platform"] or None,
            is_control=(i == 0),
            variant_metadata=json.dumps({"auto_generated": True, "source_index": i}),
        )
        session.add(variant)
        created.append(variant)

    session.commit()
    for v in created:
        session.refresh(v)

    return [_variant_to_response(v) for v in created]


@router.put("/{variant_id}", response_model=AdVariantResponse)
async def update_variant(
    campaign_id: int,
    variant_id: int,
    variant_in: AdVariantCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    variant = session.exec(
        select(AdVariant).where(
            AdVariant.id == variant_id, AdVariant.campaign_id == campaign_id
        )
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    update_data = variant_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(variant, key, value)

    session.add(variant)
    session.commit()
    session.refresh(variant)
    return _variant_to_response(variant)


@router.delete("/{variant_id}")
async def delete_variant(
    campaign_id: int,
    variant_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    variant = session.exec(
        select(AdVariant).where(
            AdVariant.id == variant_id, AdVariant.campaign_id == campaign_id
        )
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    session.delete(variant)
    session.commit()
    return {"message": "Variant deleted successfully"}
