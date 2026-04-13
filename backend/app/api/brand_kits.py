import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import (
    BrandKit,
    BrandKitCreate,
    BrandKitUpdate,
    BrandKitResponse,
    User,
)
from app.core.auth import get_current_user
from app.core.rate_limit import limiter

router = APIRouter(prefix="/brand-kits", tags=["brand-kits"])


def _to_response(kit: BrandKit) -> BrandKitResponse:
    try:
        values = json.loads(kit.brand_values) if kit.brand_values else []
    except (json.JSONDecodeError, TypeError):
        values = []
    return BrandKitResponse(
        id=kit.id,  # type: ignore[arg-type]
        user_id=kit.user_id,
        name=kit.name,
        is_default=kit.is_default,
        logo_url=kit.logo_url,
        primary_color=kit.primary_color,
        secondary_color=kit.secondary_color,
        accent_color=kit.accent_color,
        font_heading=kit.font_heading,
        font_body=kit.font_body,
        tone_of_voice=kit.tone_of_voice,
        brand_values=values,
        target_audience=kit.target_audience,
        guidelines=kit.guidelines,
        created_at=kit.created_at,
        updated_at=kit.updated_at,
    )


@router.get("/", response_model=list[BrandKitResponse])
@limiter.limit("60/minute")
async def list_brand_kits(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(BrandKit).where(BrandKit.user_id == current_user.id)
    kits = session.exec(statement).all()
    return [_to_response(k) for k in kits]


@router.get("/{brand_kit_id}", response_model=BrandKitResponse)
@limiter.limit("60/minute")
async def get_brand_kit(
    brand_kit_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    kit = session.get(BrandKit, brand_kit_id)
    if not kit or kit.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Brand kit not found")
    return _to_response(kit)


@router.post("/", response_model=BrandKitResponse, status_code=201)
@limiter.limit("10/minute")
async def create_brand_kit(
    brand_kit_in: BrandKitCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if brand_kit_in.is_default:
        statement = select(BrandKit).where(
            BrandKit.user_id == current_user.id, BrandKit.is_default == True
        )
        for existing in session.exec(statement).all():
            existing.is_default = False
            session.add(existing)

    kit = BrandKit(
        user_id=current_user.id,  # type: ignore[arg-type]
        name=brand_kit_in.name,
        is_default=brand_kit_in.is_default,
        logo_url=brand_kit_in.logo_url,
        primary_color=brand_kit_in.primary_color,
        secondary_color=brand_kit_in.secondary_color,
        accent_color=brand_kit_in.accent_color,
        font_heading=brand_kit_in.font_heading,
        font_body=brand_kit_in.font_body,
        tone_of_voice=brand_kit_in.tone_of_voice,
        brand_values=json.dumps(brand_kit_in.brand_values),
        target_audience=brand_kit_in.target_audience,
        guidelines=brand_kit_in.guidelines,
    )
    session.add(kit)
    session.commit()
    session.refresh(kit)
    return _to_response(kit)


@router.put("/{brand_kit_id}", response_model=BrandKitResponse)
@limiter.limit("20/minute")
async def update_brand_kit(
    brand_kit_id: int,
    brand_kit_in: BrandKitUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    kit = session.get(BrandKit, brand_kit_id)
    if not kit or kit.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Brand kit not found")

    update_data = brand_kit_in.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        statement = select(BrandKit).where(
            BrandKit.user_id == current_user.id,
            BrandKit.is_default == True,
            BrandKit.id != brand_kit_id,
        )
        for existing in session.exec(statement).all():
            existing.is_default = False
            session.add(existing)

    if "brand_values" in update_data:
        update_data["brand_values"] = json.dumps(update_data["brand_values"])

    for key, value in update_data.items():
        setattr(kit, key, value)

    from app.models.models import utc_now

    kit.updated_at = utc_now()
    session.add(kit)
    session.commit()
    session.refresh(kit)
    return _to_response(kit)


@router.delete("/{brand_kit_id}", status_code=204)
@limiter.limit("20/minute")
async def delete_brand_kit(
    brand_kit_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    kit = session.get(BrandKit, brand_kit_id)
    if not kit or kit.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Brand kit not found")
    session.delete(kit)
    session.commit()
