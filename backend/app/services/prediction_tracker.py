import json
import logging
from datetime import datetime, UTC
from typing import Optional

from sqlmodel import Session, select

from app.models.models import (
    Asset,
    AdPerformance,
    PredictionComparison,
)

logger = logging.getLogger(__name__)


def _avg(values: list[float]) -> Optional[float]:
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def extract_predictions(
    campaign_id: int, session: Session
) -> Optional[dict[str, Optional[float]]]:
    assets = session.exec(select(Asset).where(Asset.campaign_id == campaign_id)).all()

    predicted_ctrs: list[float] = []
    predicted_engagement_rates: list[float] = []
    predicted_quality_scores: list[float] = []
    predicted_conversion_rates: list[float] = []

    for asset in assets:
        try:
            meta = json.loads(asset.asset_metadata or "{}")
        except (json.JSONDecodeError, TypeError):
            continue

        if "predicted_ctr" in meta:
            predicted_ctrs.append(float(meta["predicted_ctr"]))
        if "predicted_engagement_rate" in meta:
            predicted_engagement_rates.append(float(meta["predicted_engagement_rate"]))
        if "predicted_quality_score" in meta:
            predicted_quality_scores.append(float(meta["predicted_quality_score"]))
        if "predicted_conversion_rate" in meta:
            predicted_conversion_rates.append(float(meta["predicted_conversion_rate"]))

    if not predicted_ctrs and not predicted_engagement_rates:
        return None

    return {
        "predicted_ctr": _avg(predicted_ctrs),
        "predicted_engagement_rate": _avg(predicted_engagement_rates),
        "predicted_conversion_rate": _avg(predicted_conversion_rates),
        "predicted_quality_score": _avg(predicted_quality_scores),
    }


def compute_accuracy(
    predicted: Optional[float], actual: Optional[float]
) -> Optional[float]:
    if predicted is None or actual is None:
        return None
    denominator = max(abs(predicted), abs(actual), 0.001)
    accuracy = 100 - abs(predicted - actual) / denominator * 100
    return max(0.0, min(100.0, accuracy))


def sync_predictions(
    campaign_id: int, user_id: int, session: Session
) -> PredictionComparison:
    predicted = extract_predictions(campaign_id, session)

    perf_entries = session.exec(
        select(AdPerformance).where(
            AdPerformance.campaign_id == campaign_id,
            AdPerformance.user_id == user_id,
        )
    ).all()

    actual_ctr: Optional[float] = None
    actual_engagement_rate: Optional[float] = None
    actual_conversion_rate: Optional[float] = None
    actual_impressions: Optional[int] = None
    actual_clicks: Optional[int] = None
    actual_conversions: Optional[int] = None

    if perf_entries:
        total_impressions = sum(e.impressions for e in perf_entries)
        total_clicks = sum(e.clicks for e in perf_entries)
        total_conversions = sum(e.conversions for e in perf_entries)

        actual_impressions = total_impressions
        actual_clicks = total_clicks
        actual_conversions = total_conversions

        if total_impressions > 0:
            actual_ctr = total_clicks / total_impressions
            actual_conversion_rate = total_conversions / total_impressions

        actual_engagement_rate = actual_ctr

    pred_ctr = predicted["predicted_ctr"] if predicted else None
    pred_engagement = predicted["predicted_engagement_rate"] if predicted else None
    pred_conversion = predicted["predicted_conversion_rate"] if predicted else None
    pred_quality = predicted["predicted_quality_score"] if predicted else None

    accuracy_scores: list[float] = []
    ctr_acc = compute_accuracy(pred_ctr, actual_ctr)
    if ctr_acc is not None:
        accuracy_scores.append(ctr_acc)
    eng_acc = compute_accuracy(pred_engagement, actual_engagement_rate)
    if eng_acc is not None:
        accuracy_scores.append(eng_acc)
    conv_acc = compute_accuracy(pred_conversion, actual_conversion_rate)
    if conv_acc is not None:
        accuracy_scores.append(conv_acc)

    accuracy_score = _avg(accuracy_scores)
    ctr_deviation = (
        (pred_ctr - actual_ctr)
        if pred_ctr is not None and actual_ctr is not None
        else None
    )

    existing = session.exec(
        select(PredictionComparison).where(
            PredictionComparison.campaign_id == campaign_id,
            PredictionComparison.user_id == user_id,
        )
    ).first()

    now = datetime.now(UTC)

    if existing:
        existing.predicted_ctr = pred_ctr
        existing.predicted_engagement_rate = pred_engagement
        existing.predicted_conversion_rate = pred_conversion
        existing.predicted_quality_score = pred_quality
        existing.actual_ctr = actual_ctr
        existing.actual_engagement_rate = actual_engagement_rate
        existing.actual_conversion_rate = actual_conversion_rate
        existing.actual_impressions = actual_impressions
        existing.actual_clicks = actual_clicks
        existing.actual_conversions = actual_conversions
        existing.accuracy_score = accuracy_score
        existing.ctr_deviation = ctr_deviation
        existing.last_synced_at = now
        existing.updated_at = now
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    comparison = PredictionComparison(
        campaign_id=campaign_id,
        user_id=user_id,
        predicted_ctr=pred_ctr,
        predicted_engagement_rate=pred_engagement,
        predicted_conversion_rate=pred_conversion,
        predicted_quality_score=pred_quality,
        actual_ctr=actual_ctr,
        actual_engagement_rate=actual_engagement_rate,
        actual_conversion_rate=actual_conversion_rate,
        actual_impressions=actual_impressions,
        actual_clicks=actual_clicks,
        actual_conversions=actual_conversions,
        accuracy_score=accuracy_score,
        ctr_deviation=ctr_deviation,
        last_synced_at=now,
    )
    session.add(comparison)
    session.commit()
    session.refresh(comparison)
    return comparison
