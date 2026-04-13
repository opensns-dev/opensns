from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlmodel import Session, select, col

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    User,
    Campaign,
    AdPerformance,
    AdPerformanceSource,
    AdPerformanceResponse,
    AdPerformanceSummary,
)

router = APIRouter(tags=["analytics"])


class AdPerformanceCreate(BaseModel):
    source: AdPerformanceSource
    date: datetime
    impressions: int
    clicks: int
    conversions: int
    spend_cents: int
    revenue_cents: int


def verify_campaign_ownership(
    campaign_id: int, user: User, session: Session
) -> Campaign:
    campaign = session.exec(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/{campaign_id}/analytics", response_model=List[AdPerformanceResponse])
@limiter.limit("60/minute")
async def get_campaign_analytics(
    request: Request,
    campaign_id: int,
    source: Optional[AdPerformanceSource] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)

    query = select(AdPerformance).where(
        AdPerformance.campaign_id == campaign_id,
        AdPerformance.user_id == user.id,
    )

    if source:
        query = query.where(AdPerformance.source == source)
    if from_date:
        query = query.where(AdPerformance.date >= datetime.fromisoformat(from_date))
    if to_date:
        query = query.where(AdPerformance.date <= datetime.fromisoformat(to_date))

    query = query.order_by(col(AdPerformance.date).desc())
    entries = session.exec(query).all()
    return entries


@router.get("/{campaign_id}/analytics/summary", response_model=AdPerformanceSummary)
@limiter.limit("60/minute")
async def get_campaign_analytics_summary(
    request: Request,
    campaign_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)

    entries = session.exec(
        select(AdPerformance).where(
            AdPerformance.campaign_id == campaign_id,
            AdPerformance.user_id == user.id,
        )
    ).all()

    if not entries:
        return AdPerformanceSummary(
            total_impressions=0,
            total_clicks=0,
            total_conversions=0,
            total_spend_cents=0,
            total_revenue_cents=0,
            avg_ctr=None,
            avg_cpc_cents=None,
            avg_roas=None,
            days_tracked=0,
        )

    total_impressions = sum(e.impressions for e in entries)
    total_clicks = sum(e.clicks for e in entries)
    total_conversions = sum(e.conversions for e in entries)
    total_spend = sum(e.spend_cents for e in entries)
    total_revenue = sum(e.revenue_cents for e in entries)
    unique_days = len({e.date.date() for e in entries})

    avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else None
    avg_cpc = int(total_spend / total_clicks) if total_clicks > 0 else None
    avg_roas = (total_revenue / total_spend) if total_spend > 0 else None

    return AdPerformanceSummary(
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        total_spend_cents=total_spend,
        total_revenue_cents=total_revenue,
        avg_ctr=avg_ctr,
        avg_cpc_cents=avg_cpc,
        avg_roas=avg_roas,
        days_tracked=unique_days,
    )


@router.post("/{campaign_id}/analytics", response_model=AdPerformanceResponse)
@limiter.limit("30/minute")
async def add_performance_entry(
    request: Request,
    campaign_id: int,
    data: AdPerformanceCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)

    ctr = (data.clicks / data.impressions) if data.impressions > 0 else None
    cpc_cents = int(data.spend_cents / data.clicks) if data.clicks > 0 else None
    cpa_cents = (
        int(data.spend_cents / data.conversions) if data.conversions > 0 else None
    )
    roas = (data.revenue_cents / data.spend_cents) if data.spend_cents > 0 else None

    entry = AdPerformance(
        campaign_id=campaign_id,
        user_id=user.id,  # type: ignore[arg-type]
        source=data.source,
        date=data.date,
        impressions=data.impressions,
        clicks=data.clicks,
        conversions=data.conversions,
        spend_cents=data.spend_cents,
        revenue_cents=data.revenue_cents,
        ctr=ctr,
        cpc_cents=cpc_cents,
        cpa_cents=cpa_cents,
        roas=roas,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{campaign_id}/analytics/{entry_id}")
@limiter.limit("30/minute")
async def delete_performance_entry(
    request: Request,
    campaign_id: int,
    entry_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)

    entry = session.exec(
        select(AdPerformance).where(
            AdPerformance.id == entry_id,
            AdPerformance.campaign_id == campaign_id,
            AdPerformance.user_id == user.id,
        )
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Performance entry not found")

    session.delete(entry)
    session.commit()
    return {"message": "Performance entry deleted"}
