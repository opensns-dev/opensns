import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import Session, select, func, col
from slowapi.util import get_remote_address

from app.db import get_session
from app.models.models import (
    AdServingEvent,
    AdServingStats,
    AdServingStatus,
    AdUnit,
    AdUnitCreate,
    AdUnitResponse,
    AdUnitUpdate,
    Asset,
    Campaign,
    User,
)
from app.core.auth import get_current_user
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns/{campaign_id}/ad-units", tags=["ad-serving"])

# NOTE: serve_router must be registered in main.py with prefix "/serve"
serve_router = APIRouter(prefix="/serve", tags=["ad-serving-public"])


def _get_campaign_or_404(session: Session, campaign_id: int, user_id: int) -> Campaign:
    campaign = session.exec(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def _unit_to_response(unit: AdUnit) -> AdUnitResponse:
    ctr = None
    if unit.total_impressions > 0:
        ctr = round(unit.total_clicks / unit.total_impressions * 100, 2)
    return AdUnitResponse(
        id=unit.id,
        campaign_id=unit.campaign_id,
        name=unit.name,
        embed_code=unit.embed_code,
        target_url=unit.target_url,
        asset_id=unit.asset_id,
        status=unit.status,
        starts_at=unit.starts_at,
        ends_at=unit.ends_at,
        total_impressions=unit.total_impressions,
        total_clicks=unit.total_clicks,
        daily_impression_cap=unit.daily_impression_cap,
        daily_click_cap=unit.daily_click_cap,
        ctr=ctr,
        created_at=unit.created_at,
    )


def _generate_embed_code(unit_id: int) -> str:
    return (
        f'<div id="opensns-ad-{unit_id}">'
        f'<a href="/serve/{unit_id}/click">'
        f'<img src="/serve/{unit_id}" />'
        f"</a></div>"
    )


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()


def _validate_target_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400, detail="target_url must use http or https scheme"
        )


def _today_event_count(session: Session, ad_unit_id: int, event_type: str) -> int:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    count = session.exec(
        select(func.count(col(AdServingEvent.id))).where(
            AdServingEvent.ad_unit_id == ad_unit_id,
            AdServingEvent.event_type == event_type,
            AdServingEvent.created_at >= today_start,
        )
    ).one()
    return count or 0


@router.get("/", response_model=List[AdUnitResponse])
async def list_ad_units(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    units = session.exec(
        select(AdUnit).where(
            AdUnit.campaign_id == campaign_id,
            AdUnit.user_id == current_user.id,
            AdUnit.status != AdServingStatus.ARCHIVED,
        )
    ).all()
    return [_unit_to_response(u) for u in units]


@router.post("/", response_model=AdUnitResponse)
@limiter.limit("20/minute")
async def create_ad_unit(
    request: Request,
    campaign_id: int,
    unit_in: AdUnitCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    _validate_target_url(unit_in.target_url)
    if unit_in.asset_id:
        asset = session.exec(
            select(Asset).where(
                Asset.id == unit_in.asset_id, Asset.campaign_id == campaign_id
            )
        ).first()
        if not asset:
            raise HTTPException(
                status_code=404, detail="Asset not found in this campaign"
            )
    unit = AdUnit(
        user_id=current_user.id,
        campaign_id=campaign_id,
        name=unit_in.name,
        target_url=unit_in.target_url,
        asset_id=unit_in.asset_id,
        starts_at=unit_in.starts_at,
        ends_at=unit_in.ends_at,
        daily_impression_cap=unit_in.daily_impression_cap,
        daily_click_cap=unit_in.daily_click_cap,
    )
    session.add(unit)
    session.commit()
    session.refresh(unit)
    unit.embed_code = _generate_embed_code(unit.id)
    session.add(unit)
    session.commit()
    session.refresh(unit)
    return _unit_to_response(unit)


@router.put("/{unit_id}", response_model=AdUnitResponse)
@limiter.limit("20/minute")
async def update_ad_unit(
    request: Request,
    campaign_id: int,
    unit_id: int,
    unit_in: AdUnitUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    unit = session.exec(
        select(AdUnit).where(
            AdUnit.id == unit_id,
            AdUnit.campaign_id == campaign_id,
            AdUnit.user_id == current_user.id,
        )
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Ad unit not found")
    update_data = unit_in.model_dump(exclude_unset=True)
    if "target_url" in update_data and update_data["target_url"]:
        _validate_target_url(update_data["target_url"])
    for key, value in update_data.items():
        setattr(unit, key, value)
    unit.updated_at = datetime.now(timezone.utc)
    session.add(unit)
    session.commit()
    session.refresh(unit)
    return _unit_to_response(unit)


@router.delete("/{unit_id}")
async def delete_ad_unit(
    campaign_id: int,
    unit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    unit = session.exec(
        select(AdUnit).where(
            AdUnit.id == unit_id,
            AdUnit.campaign_id == campaign_id,
            AdUnit.user_id == current_user.id,
        )
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Ad unit not found")
    unit.status = AdServingStatus.ARCHIVED
    unit.updated_at = datetime.now(timezone.utc)
    session.add(unit)
    session.commit()
    return {"message": "Ad unit archived"}


@router.get("/{unit_id}/stats", response_model=AdServingStats)
async def get_ad_unit_stats(
    campaign_id: int,
    unit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_campaign_or_404(session, campaign_id, current_user.id)
    unit = session.exec(
        select(AdUnit).where(
            AdUnit.id == unit_id,
            AdUnit.campaign_id == campaign_id,
            AdUnit.user_id == current_user.id,
        )
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Ad unit not found")
    impressions_today = _today_event_count(session, unit_id, "impression")
    clicks_today = _today_event_count(session, unit_id, "click")
    ctr = None
    if unit.total_impressions > 0:
        ctr = round(unit.total_clicks / unit.total_impressions * 100, 2)
    return AdServingStats(
        ad_unit_id=unit.id,
        total_impressions=unit.total_impressions,
        total_clicks=unit.total_clicks,
        ctr=ctr,
        impressions_today=impressions_today,
        clicks_today=clicks_today,
    )


@serve_router.get("/{unit_id}")
@limiter.limit("1000/minute")
async def serve_ad(
    request: Request,
    unit_id: int,
    session: Session = Depends(get_session),
):
    unit = session.exec(select(AdUnit).where(AdUnit.id == unit_id)).first()
    if not unit or unit.status != AdServingStatus.ACTIVE:
        return JSONResponse(status_code=204, content=None)

    now = datetime.now(timezone.utc)
    if unit.starts_at and now < unit.starts_at:
        return JSONResponse(status_code=204, content=None)
    if unit.ends_at and now > unit.ends_at:
        return JSONResponse(status_code=204, content=None)

    if unit.daily_impression_cap:
        today_impressions = _today_event_count(session, unit_id, "impression")
        if today_impressions >= unit.daily_impression_cap:
            return JSONResponse(status_code=204, content=None)

    ip_hash = _hash_ip(get_remote_address(request))
    event = AdServingEvent(
        ad_unit_id=unit_id,
        event_type="impression",
        ip_hash=ip_hash,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    session.add(event)
    unit.total_impressions += 1
    session.add(unit)
    session.commit()

    asset_url: Optional[str] = None
    if unit.asset_id:
        asset = session.get(Asset, unit.asset_id)
        if asset:
            asset_url = asset.content

    return JSONResponse(
        content={
            "ad_unit_id": unit.id,
            "target_url": unit.target_url,
            "asset_url": asset_url,
        }
    )


@serve_router.get("/{unit_id}/click")
@limiter.limit("1000/minute")
async def serve_click(
    request: Request,
    unit_id: int,
    session: Session = Depends(get_session),
):
    unit = session.exec(select(AdUnit).where(AdUnit.id == unit_id)).first()
    if not unit or unit.status != AdServingStatus.ACTIVE:
        return JSONResponse(status_code=204, content=None)

    if unit.daily_click_cap:
        today_clicks = _today_event_count(session, unit_id, "click")
        if today_clicks >= unit.daily_click_cap:
            return JSONResponse(status_code=204, content=None)

    ip_hash = _hash_ip(get_remote_address(request))
    event = AdServingEvent(
        ad_unit_id=unit_id,
        event_type="click",
        ip_hash=ip_hash,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    session.add(event)
    unit.total_clicks += 1
    session.add(unit)
    session.commit()

    return RedirectResponse(url=unit.target_url, status_code=302)
