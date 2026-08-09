import hmac
import json
import re
from calendar import monthrange
from datetime import UTC, datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo, available_timezones

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy import func, text
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    AUTOPILOT_SCHEDULE_LIMITS,
    AutopilotCadence,
    AutopilotRule,
    AutopilotRuleCreate,
    AutopilotRuleUpdate,
    AutopilotRuleResponse,
    AutopilotRunLog,
    AutopilotRunLogResponse,
    AutopilotRunStatus,
    Campaign,
    CampaignStatus,
    PlanTier,
    User,
    utc_now,
)
from app.services.pipeline import run_campaign_pipeline
from app.services.autopilot import compute_next_run as _compute_next_run_for_rule
from app.services.usage import get_or_create_subscription

router = APIRouter(prefix="/autopilot", tags=["autopilot"])
VALID_TIMEZONES = available_timezones()
VALID_ASSET_TYPES = {"image", "video", "ugc"}


def _validate_asset_types(asset_types: list[str] | None) -> None:
    if asset_types is None:
        return
    if not asset_types:
        raise HTTPException(status_code=400, detail="asset_types must not be empty")
    if "image" not in asset_types:
        raise HTTPException(status_code=400, detail='asset_types must contain "image"')
    invalid = set(asset_types) - VALID_ASSET_TYPES
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid asset_types: {sorted(invalid)}. Valid: {sorted(VALID_ASSET_TYPES)}",
        )


def _parse_json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _to_response(rule: AutopilotRule) -> AutopilotRuleResponse:
    return AutopilotRuleResponse.model_validate(rule)


def _to_log_response(log: AutopilotRunLog) -> AutopilotRunLogResponse:
    return AutopilotRunLogResponse.model_validate(log)


def _parse_time_of_day(time_of_day: str) -> tuple[int, int]:
    if not re.fullmatch(r"\d{2}:\d{2}", time_of_day):
        raise HTTPException(status_code=400, detail="time_of_day must be in HH:MM format")
    try:
        parsed = datetime.strptime(time_of_day, "%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="time_of_day must be in HH:MM format") from exc
    return parsed.hour, parsed.minute


def _validate_schedule_fields(
    cadence: AutopilotCadence,
    days_of_week: Optional[List[int]],
    time_of_day: str,
    timezone: str,
    num_variations: int,
) -> None:
    if timezone not in VALID_TIMEZONES:
        raise HTTPException(status_code=400, detail="timezone must be a valid IANA timezone")

    if num_variations < 1 or num_variations > 10:
        raise HTTPException(status_code=400, detail="num_variations must be between 1 and 10")

    hour, minute = _parse_time_of_day(time_of_day)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise HTTPException(status_code=400, detail="time_of_day must be in HH:MM format")

    if cadence == AutopilotCadence.WEEKLY:
        if not days_of_week:
            raise HTTPException(
                status_code=400,
                detail="days_of_week is required for weekly cadence",
            )
        if any(day < 0 or day > 6 for day in days_of_week):
            raise HTTPException(
                status_code=400,
                detail="days_of_week values must be between 0 and 6",
            )

    if cadence == AutopilotCadence.MONTHLY and days_of_week:
        if any(day < 1 or day > 31 for day in days_of_week):
            raise HTTPException(
                status_code=400,
                detail="days_of_week values must be between 1 and 31 for monthly cadence",
            )


def _compute_next_run_from_params(
    cadence: AutopilotCadence,
    days_of_week: Optional[List[int]],
    time_of_day: str,
    timezone: str,
) -> datetime:
    """Adapter for API: build a minimal rule-like object and delegate to service."""
    from types import SimpleNamespace

    fake_rule = SimpleNamespace(
        cadence=cadence,
        days_of_week=json.dumps(days_of_week) if days_of_week else None,
        time_of_day=time_of_day,
        timezone=timezone,
    )
    return _compute_next_run_for_rule(fake_rule)  # type: ignore[arg-type]


def _get_owned_rule(session: Session, current_user: User, rule_id: int) -> AutopilotRule:
    rule = session.exec(
        select(AutopilotRule).where(
            AutopilotRule.id == rule_id,
            AutopilotRule.user_id == current_user.id,
        )
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Autopilot rule not found")
    return rule


@router.post("/rules", response_model=AutopilotRuleResponse)
@limiter.limit("30/minute")
async def create_rule(
    request: Request,
    data: AutopilotRuleCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _validate_schedule_fields(
        data.cadence,
        data.days_of_week,
        data.time_of_day,
        data.timezone,
        data.num_variations,
    )
    _validate_asset_types(data.asset_types)

    if data.auto_publish and not data.publish_connection_ids:
        raise HTTPException(
            status_code=400,
            detail="publish_connection_ids required when auto_publish is enabled",
        )

    subscription = get_or_create_subscription(session, current_user)
    plan = subscription.tier
    limit = AUTOPILOT_SCHEDULE_LIMITS.get(plan, 0)

    if limit == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "autopilot_plan_required",
                "message": "Autopilot requires Basic plan or higher",
                "upgrade_url": "/billing",
            },
        )

    existing_count_result = session.exec(
        select(func.count()).select_from(AutopilotRule).where(
            AutopilotRule.user_id == current_user.id
        )
    ).one()
    existing_count = int(existing_count_result or 0)

    if existing_count >= limit:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "autopilot_limit_reached",
                "message": f"Your plan allows {limit} autopilot schedule(s). Upgrade for more.",
                "current": existing_count,
                "limit": limit,
            },
        )

    rule = AutopilotRule(
        user_id=current_user.id,  # type: ignore[arg-type]
        enabled=True,
        timezone=data.timezone,
        cadence=data.cadence,
        days_of_week=json.dumps(data.days_of_week) if data.days_of_week is not None else None,
        time_of_day=data.time_of_day,
        next_run_at=_compute_next_run_from_params(
            data.cadence, data.days_of_week, data.time_of_day, data.timezone
        ),
        product_url=data.product_url,
        brand_kit_id=data.brand_kit_id,
        platform_targets=json.dumps(data.platform_targets),
        asset_types=json.dumps(data.asset_types) if data.asset_types else '["image"]',
        num_variations=data.num_variations,
        requires_approval=data.requires_approval if data.requires_approval is not None else True,
        approval_timeout_hours=48,
        auto_publish=data.auto_publish if data.auto_publish is not None else False,
        publish_connection_ids=json.dumps(data.publish_connection_ids) if data.publish_connection_ids else None,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return _to_response(rule)


@router.get("/rules", response_model=List[AutopilotRuleResponse])
@limiter.limit("60/minute")
async def list_rules(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rules = session.exec(
        select(AutopilotRule)
        .where(AutopilotRule.user_id == current_user.id)
        .order_by(text("created_at DESC"))
    ).all()
    return [_to_response(rule) for rule in rules]


@router.get("/rules/{rule_id}", response_model=AutopilotRuleResponse)
@limiter.limit("60/minute")
async def get_rule(
    request: Request,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rule = _get_owned_rule(session, current_user, rule_id)
    return _to_response(rule)


@router.put("/rules/{rule_id}", response_model=AutopilotRuleResponse)
@limiter.limit("30/minute")
async def update_rule(
    request: Request,
    rule_id: int,
    data: AutopilotRuleUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rule = _get_owned_rule(session, current_user, rule_id)

    new_cadence = data.cadence or rule.cadence
    new_days_of_week = data.days_of_week
    if new_days_of_week is None and rule.days_of_week:
        new_days_of_week = json.loads(rule.days_of_week)
    new_time_of_day = data.time_of_day or rule.time_of_day
    new_timezone = data.timezone or rule.timezone
    new_num_variations = data.num_variations or rule.num_variations

    _validate_schedule_fields(
        new_cadence,
        new_days_of_week,
        new_time_of_day,
        new_timezone,
        new_num_variations,
    )
    _validate_asset_types(data.asset_types)

    if data.auto_publish is True and not data.publish_connection_ids:
        current_ids = _parse_json_list(rule.publish_connection_ids)
        if not current_ids:
            raise HTTPException(
                status_code=400,
                detail="publish_connection_ids required when auto_publish is enabled",
            )

    if data.platform_targets is not None:
        rule.platform_targets = json.dumps(data.platform_targets)
    if data.cadence is not None:
        rule.cadence = data.cadence
    if data.days_of_week is not None:
        rule.days_of_week = json.dumps(data.days_of_week)
    if data.time_of_day is not None:
        rule.time_of_day = data.time_of_day
    if data.timezone is not None:
        rule.timezone = data.timezone
    if data.num_variations is not None:
        rule.num_variations = data.num_variations
    if data.brand_kit_id is not None:
        rule.brand_kit_id = data.brand_kit_id
    if data.product_url is not None:
        rule.product_url = data.product_url
    if data.asset_types is not None:
        rule.asset_types = json.dumps(data.asset_types)
    if data.requires_approval is not None:
        rule.requires_approval = data.requires_approval
    if data.auto_publish is not None:
        rule.auto_publish = data.auto_publish
    if data.publish_connection_ids is not None:
        rule.publish_connection_ids = json.dumps(data.publish_connection_ids)

    rule.next_run_at = _compute_next_run_from_params(
        new_cadence, new_days_of_week, new_time_of_day, new_timezone
    )
    rule.updated_at = utc_now()

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return _to_response(rule)


@router.delete("/rules/{rule_id}")
@limiter.limit("30/minute")
async def delete_rule(
    request: Request,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rule = _get_owned_rule(session, current_user, rule_id)
    session.delete(rule)
    session.commit()
    return {"message": "Autopilot rule deleted"}


@router.post("/rules/{rule_id}/toggle", response_model=AutopilotRuleResponse)
@limiter.limit("30/minute")
async def toggle_rule(
    request: Request,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rule = _get_owned_rule(session, current_user, rule_id)
    rule.enabled = not rule.enabled
    if rule.enabled:
        days_of_week = json.loads(rule.days_of_week) if rule.days_of_week else None
        rule.next_run_at = _compute_next_run_from_params(
            rule.cadence, days_of_week, rule.time_of_day, rule.timezone
        )
    rule.updated_at = utc_now()
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return _to_response(rule)


@router.get("/rules/{rule_id}/history", response_model=List[AutopilotRunLogResponse])
@limiter.limit("60/minute")
async def list_rule_history(
    request: Request,
    rule_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _get_owned_rule(session, current_user, rule_id)
    logs = session.exec(
        select(AutopilotRunLog)
        .where(AutopilotRunLog.rule_id == rule_id)
        .order_by(text("started_at DESC"))
    ).all()
    return [_to_log_response(log) for log in logs]


@router.post("/rules/{rule_id}/run-now", response_model=Campaign)
@limiter.limit("30/minute")
async def run_rule_now(
    request: Request,
    rule_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rule = _get_owned_rule(session, current_user, rule_id)
    campaign = Campaign(
        title=f"Autopilot: {rule.product_url}",
        product_url=rule.product_url,
        description=f"Manual autopilot run for rule {rule.id}",
        brand_kit_id=rule.brand_kit_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        status=CampaignStatus.PENDING,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    campaign_id = campaign.id
    if campaign_id is None:
        raise HTTPException(status_code=500, detail="Campaign ID missing")
    campaign_id_int = int(campaign_id)

    from app.models.models import AutopilotRunLog, AutopilotRunStatus

    if rule.id is None:
        raise HTTPException(status_code=500, detail="Autopilot rule ID missing")
    rule_id_int = int(rule.id)

    run_log = AutopilotRunLog(
        rule_id=rule_id_int,
        campaign_id=campaign_id_int,
        status=AutopilotRunStatus.RUNNING,
        credits_estimated=rule.num_variations,
    )
    session.add(run_log)
    session.commit()

    assert campaign.id is not None
    background_tasks.add_task(
        run_campaign_pipeline, campaign.id, rule.requires_approval, autopilot_run_log_id=run_log.id
    )
    return campaign

@router.post("/internal/tick")
async def internal_tick(
    request: Request,
    background_tasks: BackgroundTasks,
    x_internal_key: str = Header(..., alias="X-Internal-Key"),
    session: Session = Depends(get_session),
):
    if not hmac.compare_digest(x_internal_key, settings.INTERNAL_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid internal key")
    from app.services.autopilot import autopilot_tick
    results = autopilot_tick(session)
    for campaign_id, run_log_id, req_approval in results:
        background_tasks.add_task(
            run_campaign_pipeline, campaign_id, req_approval, autopilot_run_log_id=run_log_id
        )
    return {"executed": len(results), "campaigns": [r[0] for r in results]}
