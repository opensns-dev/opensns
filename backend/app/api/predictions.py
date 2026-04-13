from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    User,
    Campaign,
    PredictionComparison,
    PredictionComparisonResponse,
    PredictionAccuracySummary,
)
from app.services.prediction_tracker import sync_predictions

router = APIRouter(tags=["predictions"])


def verify_campaign_ownership(
    campaign_id: int, user: User, session: Session
) -> Campaign:
    campaign = session.exec(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


class ActualsUpdate(BaseModel):
    actual_ctr: Optional[float] = None
    actual_engagement_rate: Optional[float] = None
    actual_conversion_rate: Optional[float] = None
    actual_impressions: Optional[int] = None
    actual_clicks: Optional[int] = None
    actual_conversions: Optional[int] = None


@router.get("/{campaign_id}/predictions", response_model=PredictionComparisonResponse)
@limiter.limit("60/minute")
async def get_predictions(
    request: Request,
    campaign_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)

    comparison = session.exec(
        select(PredictionComparison).where(
            PredictionComparison.campaign_id == campaign_id,
            PredictionComparison.user_id == user.id,
        )
    ).first()

    if not comparison:
        raise HTTPException(status_code=404, detail="No prediction data found")

    return comparison


@router.post(
    "/{campaign_id}/predictions/sync", response_model=PredictionComparisonResponse
)
@limiter.limit("10/minute")
async def sync_campaign_predictions(
    request: Request,
    campaign_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)
    comparison = sync_predictions(campaign_id, user.id, session)  # type: ignore[arg-type]
    return comparison


@router.put(
    "/{campaign_id}/predictions/actuals", response_model=PredictionComparisonResponse
)
@limiter.limit("30/minute")
async def update_actuals(
    request: Request,
    campaign_id: int,
    data: ActualsUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    verify_campaign_ownership(campaign_id, user, session)

    comparison = session.exec(
        select(PredictionComparison).where(
            PredictionComparison.campaign_id == campaign_id,
            PredictionComparison.user_id == user.id,
        )
    ).first()

    if not comparison:
        comparison = PredictionComparison(
            campaign_id=campaign_id,
            user_id=user.id,  # type: ignore[arg-type]
        )

    if data.actual_ctr is not None:
        comparison.actual_ctr = data.actual_ctr
    if data.actual_engagement_rate is not None:
        comparison.actual_engagement_rate = data.actual_engagement_rate
    if data.actual_conversion_rate is not None:
        comparison.actual_conversion_rate = data.actual_conversion_rate
    if data.actual_impressions is not None:
        comparison.actual_impressions = data.actual_impressions
    if data.actual_clicks is not None:
        comparison.actual_clicks = data.actual_clicks
    if data.actual_conversions is not None:
        comparison.actual_conversions = data.actual_conversions

    from app.services.prediction_tracker import compute_accuracy, _avg
    from datetime import datetime, UTC

    accuracy_scores: list[float] = []
    ctr_acc = compute_accuracy(comparison.predicted_ctr, comparison.actual_ctr)
    if ctr_acc is not None:
        accuracy_scores.append(ctr_acc)
    eng_acc = compute_accuracy(
        comparison.predicted_engagement_rate, comparison.actual_engagement_rate
    )
    if eng_acc is not None:
        accuracy_scores.append(eng_acc)
    conv_acc = compute_accuracy(
        comparison.predicted_conversion_rate, comparison.actual_conversion_rate
    )
    if conv_acc is not None:
        accuracy_scores.append(conv_acc)

    comparison.accuracy_score = _avg(accuracy_scores)
    comparison.ctr_deviation = (
        (comparison.predicted_ctr - comparison.actual_ctr)
        if comparison.predicted_ctr is not None and comparison.actual_ctr is not None
        else None
    )
    comparison.updated_at = datetime.now(UTC)

    session.add(comparison)
    session.commit()
    session.refresh(comparison)
    return comparison


@router.get(
    "/predictions/summary",
    response_model=PredictionAccuracySummary,
)
@limiter.limit("60/minute")
async def get_prediction_summary(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    comparisons = session.exec(
        select(PredictionComparison).where(
            PredictionComparison.user_id == user.id,
        )
    ).all()

    if not comparisons:
        return PredictionAccuracySummary(
            total_campaigns=0,
            avg_accuracy_score=None,
            avg_ctr_deviation=None,
            best_accuracy_campaign_id=None,
            worst_accuracy_campaign_id=None,
            prediction_count=0,
        )

    campaign_ids = {c.campaign_id for c in comparisons}
    accuracy_scores = [
        c.accuracy_score for c in comparisons if c.accuracy_score is not None
    ]
    ctr_deviations = [
        c.ctr_deviation for c in comparisons if c.ctr_deviation is not None
    ]

    avg_accuracy = (
        sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None
    )
    avg_ctr_dev = sum(ctr_deviations) / len(ctr_deviations) if ctr_deviations else None

    best_id = None
    worst_id = None
    scored = [c for c in comparisons if c.accuracy_score is not None]
    if scored:
        best = max(scored, key=lambda c: c.accuracy_score)  # type: ignore[arg-type]
        worst = min(scored, key=lambda c: c.accuracy_score)  # type: ignore[arg-type]
        best_id = best.campaign_id
        worst_id = worst.campaign_id

    return PredictionAccuracySummary(
        total_campaigns=len(campaign_ids),
        avg_accuracy_score=avg_accuracy,
        avg_ctr_deviation=avg_ctr_dev,
        best_accuracy_campaign_id=best_id,
        worst_accuracy_campaign_id=worst_id,
        prediction_count=len(comparisons),
    )
