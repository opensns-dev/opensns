from __future__ import annotations

import calendar
import json
from datetime import datetime, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, or_, update
from sqlmodel import Session, select

from app.models.models import (
    AutopilotCadence,
    AutopilotRunLog,
    AutopilotRunStatus,
    AutopilotRule,
    Campaign,
    CampaignStatus,
    NotificationType,
    User,
    utc_now,
)
from app.services.email import (
    send_autopilot_approval_needed,
    send_autopilot_credits_insufficient,
    send_autopilot_run_failed,
)
from app.services.notifications import create_notification
from app.services.usage import (
    estimate_workflow_credits,
    has_sufficient_credits as _has_sufficient_credits_for_user,
)

MAX_CONCURRENT_PER_USER = 2
MAX_CONSECUTIVE_FAILURES = 5
LOCK_TTL_MINUTES = 30
BACKOFF_MINUTES = [5, 15, 45]  # Escalating delays for transient errors
MAX_TRANSIENT_RETRIES = 3  # Cap retries for transient errors; after this count, backoff saturates at max delay

RULE_COLS = cast(Any, getattr(AutopilotRule, "__table__")).c
RUN_LOG_COLS = cast(Any, getattr(AutopilotRunLog, "__table__")).c


def classify_error(error: Exception) -> str:
    """Classify error as transient, permanent, or resource.

    NOTE: Classification uses string matching which is inherently fragile.
    Consider extending with explicit exception type checks as the codebase
    adds more specific exception classes.
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    if "insufficient_credits" in error_str or "credit" in error_str:
        return "resource"

    if any(x in error_str for x in ["timeout", "502", "503", "504", "connection", "rate limit"]):
        return "transient"
    if any(x in error_type.lower() for x in ["timeout", "connection"]):
        return "transient"

    if any(x in error_str for x in ["400", "401", "403", "404", "validation"]):
        return "permanent"

    return "transient"


def compute_backoff_next_run(rule: AutopilotRule, retry_count: int) -> datetime:
    delay_idx = min(retry_count, len(BACKOFF_MINUTES) - 1)
    delay = timedelta(minutes=BACKOFF_MINUTES[delay_idx])
    return utc_now() + delay


def _display_name(user: User) -> str:
    name = getattr(user, "name", None)
    if name:
        return name
    return user.email.split("@")[0] if user.email else "there"


def _parse_json_list(value: str | None, default: list[int] | list[str]) -> list:
    if not value:
        return list(default)
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else list(default)
    except (TypeError, json.JSONDecodeError):
        return list(default)


def _has_sufficient_credits(session: Session, user_id: int, needed: int) -> bool:
    """Adapter: load User from user_id, then delegate to usage.has_sufficient_credits."""
    user = session.get(User, user_id)
    if not user:
        return False
    return _has_sufficient_credits_for_user(session, user, needed)


def compute_next_run(rule: AutopilotRule, after: datetime | None = None) -> datetime:
    """Compute the next run time in naive UTC from rule timezone settings."""
    tz_name = rule.timezone or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

    now_utc = after or utc_now()
    now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    try:
        hour, minute = map(int, rule.time_of_day.split(":"))
    except ValueError:
        hour, minute = 9, 0

    candidate: datetime | None = None

    if rule.cadence == AutopilotCadence.DAILY:
        candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now_local:
            candidate += timedelta(days=1)

    elif rule.cadence == AutopilotCadence.WEEKLY:
        target_days = [int(day) for day in _parse_json_list(rule.days_of_week, [0])]
        current_weekday = now_local.weekday()
        today_at_time = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if current_weekday in target_days and today_at_time > now_local:
            candidate = today_at_time
        else:
            for offset in range(1, 8):
                check_day = (current_weekday + offset) % 7
                if check_day in target_days:
                    candidate = today_at_time + timedelta(days=offset)
                    break

    elif rule.cadence == AutopilotCadence.MONTHLY:
        day_values = sorted(set(int(day) for day in _parse_json_list(rule.days_of_week, [1])))
        year = now_local.year
        month = now_local.month
        for _ in range(24):  # Search up to 24 months ahead
            max_day = calendar.monthrange(year, month)[1]
            for day_of_month in day_values:
                day = min(day_of_month, max_day)
                candidate = now_local.replace(
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0,
                )
                if candidate > now_local:
                    return candidate.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            month += 1
            if month > 12:
                month = 1
                year += 1

    if candidate is None:
        candidate = now_local + timedelta(days=1)
        candidate = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now_local:
            candidate += timedelta(days=1)

    return candidate.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def try_claim_rule(session: Session, rule_id: int, now: datetime) -> bool:
    lock_expiry = now + timedelta(minutes=LOCK_TTL_MINUTES)
    stmt = (
        update(AutopilotRule)
        .where(
            RULE_COLS.id == rule_id,
            RULE_COLS.enabled.is_(True),
            RULE_COLS.next_run_at <= now,
            or_(RULE_COLS.locked_until.is_(None), RULE_COLS.locked_until < now),
        )
        .values(locked_until=lock_expiry)
    )
    result = session.exec(stmt)
    session.commit()
    return result.rowcount == 1


def create_run_log(session: Session, rule: AutopilotRule, estimated: int) -> AutopilotRunLog:
    rule_id = rule.id
    assert rule_id is not None
    log = AutopilotRunLog(
        rule_id=rule_id,
        status=AutopilotRunStatus.RUNNING,
        credits_estimated=estimated,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def handle_skip(session: Session, rule: AutopilotRule, reason: str, now: datetime) -> None:
    rule_id = rule.id
    assert rule_id is not None
    log = AutopilotRunLog(
        rule_id=rule_id,
        status=AutopilotRunStatus.SKIPPED,
        error=reason,
        completed_at=now,
    )
    session.add(log)
    rule.next_run_at = compute_next_run(rule, now)
    rule.locked_until = None
    session.add(rule)
    session.commit()


def handle_failure(
    session: Session,
    rule: AutopilotRule,
    run_log: AutopilotRunLog,
    error: Exception,
    now: datetime,
) -> None:
    error_class = classify_error(error)

    run_log.status = AutopilotRunStatus.FAILED
    run_log.error = str(error)[:500]
    run_log.completed_at = now

    if error_class == "transient":
        run_log.retry_count += 1
        # Backoff saturates at BACKOFF_MINUTES[-1] (45 min) after MAX_TRANSIENT_RETRIES attempts
        rule.next_run_at = compute_backoff_next_run(rule, run_log.retry_count)
    else:
        rule.next_run_at = compute_next_run(rule, now)

    session.add(run_log)

    rule.consecutive_failures += 1
    rule.last_failure_reason = str(error)[:200]
    rule.locked_until = None
    session.add(rule)

    if rule.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
        rule.enabled = False
        try:
            user = session.get(User, rule.user_id)
            if user and user.email:
                send_autopilot_run_failed(
                    user.email,
                    _display_name(user),
                    rule.product_url,
                    f"Autopilot disabled after {MAX_CONSECUTIVE_FAILURES} consecutive failures. Last error: {str(error)[:200]}",
                )
        except Exception:
            pass
    else:
        try:
            user = session.get(User, rule.user_id)
            if user and user.email:
                send_autopilot_run_failed(
                    user.email,
                    _display_name(user),
                    rule.product_url,
                    str(error)[:200],
                )
        except Exception:
            pass

    try:
        if rule.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            create_notification(
                session, rule.user_id, NotificationType.AUTOPILOT_DISABLED,
                "Autopilot disabled",
                f"Autopilot for {rule.product_url} disabled after {MAX_CONSECUTIVE_FAILURES} consecutive failures",
                {"rule_id": rule.id},
            )
        else:
            create_notification(
                session, rule.user_id, NotificationType.AUTOPILOT_FAILED,
                "Autopilot run failed",
                f"Campaign for {rule.product_url} failed: {str(error)[:200]}",
                {"rule_id": rule.id},
            )
    except Exception:
        pass

    session.commit()


def sweep_expired_approvals(session: Session, now: datetime) -> None:
    max_timeout_hours = 168  # 7 days, safe upper bound
    oldest_possible = now - timedelta(hours=max_timeout_hours)
    stale_logs = session.exec(
        select(AutopilotRunLog, AutopilotRule)
        .join(AutopilotRule, RUN_LOG_COLS.rule_id == RULE_COLS.id)
        .where(
            RUN_LOG_COLS.status == AutopilotRunStatus.AWAITING_APPROVAL,
            RUN_LOG_COLS.started_at < now,
            RUN_LOG_COLS.started_at > oldest_possible,
        )
    ).all()

    for log, rule in stale_logs:
        timeout = timedelta(hours=rule.approval_timeout_hours)
        if log.started_at + timeout < now:
            log.status = AutopilotRunStatus.EXPIRED
            log.completed_at = now
            rule.next_run_at = compute_next_run(rule, now)
            rule.locked_until = None
            session.add(log)
            session.add(rule)

    session.commit()


def complete_run(
    session: Session,
    run_log_id: int,
    campaign_id: int,
    status: AutopilotRunStatus,
    credits_used: int = 0,
) -> None:
    log = session.get(AutopilotRunLog, run_log_id)
    if not log:
        return
    log.status = status
    log.campaign_id = campaign_id
    log.credits_used = credits_used
    log.completed_at = utc_now()
    session.add(log)

    rule = session.get(AutopilotRule, log.rule_id)

    if status == AutopilotRunStatus.AWAITING_APPROVAL:
        try:
            if rule:
                user = session.get(User, rule.user_id)
                if user and user.email:
                    send_autopilot_approval_needed(
                        user.email,
                        _display_name(user),
                        rule.product_url,
                        campaign_id,
                    )
        except Exception:
            pass

    session.commit()

    if rule:
        try:
            if status == AutopilotRunStatus.COMPLETED:
                create_notification(
                    session, rule.user_id, NotificationType.AUTOPILOT_COMPLETE,
                    "Autopilot run completed",
                    f"Campaign for {rule.product_url} completed successfully",
                    {"campaign_id": campaign_id, "rule_id": log.rule_id},
                )
            elif status == AutopilotRunStatus.FAILED:
                create_notification(
                    session, rule.user_id, NotificationType.AUTOPILOT_FAILED,
                    "Autopilot run failed",
                    f"Campaign for {rule.product_url} failed",
                    {"campaign_id": campaign_id, "rule_id": log.rule_id},
                )
        except Exception:
            pass


def execute_autopilot_rule(
    session: Session,
    rule: AutopilotRule,
    run_log: AutopilotRunLog,
    now: datetime,
) -> tuple[int, int]:
    rule_id = rule.id
    assert rule_id is not None

    campaign = Campaign(
        title=f"Autopilot: {rule.product_url}",
        product_url=rule.product_url,
        brand_kit_id=rule.brand_kit_id,
        user_id=rule.user_id,
        status=CampaignStatus.PENDING,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    campaign_id = campaign.id
    assert campaign_id is not None

    run_log.campaign_id = campaign_id
    session.add(run_log)

    rule.last_run_at = now
    rule.run_count += 1
    rule.consecutive_failures = 0
    rule.next_run_at = compute_next_run(rule, now)
    rule.locked_until = None
    session.add(rule)
    session.commit()

    run_log_id = run_log.id
    assert run_log_id is not None
    return campaign_id, run_log_id


def autopilot_tick(session: Session) -> list[tuple[int, int, bool]]:
    """Called every minute. Executes due rules and sweeps expired approvals."""
    now = utc_now()
    campaigns_to_run: list[tuple[int, int, bool]] = []

    sweep_expired_approvals(session, now)

    due_rules = session.exec(
        select(AutopilotRule).where(
            RULE_COLS.enabled.is_(True),
            RULE_COLS.next_run_at <= now,
            or_(RULE_COLS.locked_until.is_(None), RULE_COLS.locked_until < now),
        )
    ).all()

    for rule in due_rules:
        rule_user_id = rule.user_id
        running_count = session.exec(
            select(func.count(RUN_LOG_COLS.id)).where(
                RUN_LOG_COLS.rule_id.in_(
                    select(RULE_COLS.id).where(RULE_COLS.user_id == rule_user_id)
                ),
                RUN_LOG_COLS.status == AutopilotRunStatus.RUNNING,
            )
        ).one()
        if running_count >= MAX_CONCURRENT_PER_USER:
            continue

        rule_id = rule.id
        if rule_id is None:
            continue

        if not try_claim_rule(session, rule_id, now):
            continue

        estimated = estimate_workflow_credits(rule.asset_types, rule.num_variations)
        if not _has_sufficient_credits(session, rule_user_id, estimated):
            handle_skip(session, rule, "insufficient_credits", now)
            try:
                user = session.get(User, rule_user_id)
                if user and user.email:
                    send_autopilot_credits_insufficient(
                        user.email,
                        _display_name(user),
                        rule.product_url,
                        estimated,
                    )
            except Exception:
                pass
            continue

        run_log = create_run_log(session, rule, estimated)
        try:
            campaign_id, run_log_id = execute_autopilot_rule(session, rule, run_log, now)
            campaigns_to_run.append((campaign_id, run_log_id, rule.requires_approval))
        except Exception as exc:
            handle_failure(session, rule, run_log, exc, now)

    return campaigns_to_run


async def auto_publish_for_autopilot(campaign_id: int, rule_id: int) -> None:
    import logging

    from app.db import engine as _engine

    logger = logging.getLogger(__name__)

    try:
        with Session(_engine) as session:
            rule = session.get(AutopilotRule, rule_id)
            if not rule or not rule.auto_publish:
                return

            connection_ids = _parse_json_list(rule.publish_connection_ids, [])
            if not connection_ids:
                return

            from app.core.config import settings
            from app.core.encryption import decrypt_api_key
            from app.models.models import Asset, AssetType, PublishConnection
            from app.services.publishing.meta_adapter import MetaPublishingAdapter
            from app.services.publishing.threads_adapter import ThreadsPublishingAdapter
            from app.services.publishing.x_adapter import XPublishingAdapter

            meta_adapter = MetaPublishingAdapter()
            x_adapter = XPublishingAdapter()
            threads_adapter = ThreadsPublishingAdapter()

            assets = session.exec(
                select(Asset).where(Asset.campaign_id == campaign_id)
            ).all()
            if not assets:
                return

            image_asset = next((a for a in assets if a.type == "IMAGE"), None)
            image_url = image_asset.content if image_asset else None
            copy_asset = session.exec(
                select(Asset).where(
                    Asset.campaign_id == campaign_id,
                    Asset.type == AssetType.COPY,
                )
            ).first()
            caption = copy_asset.content if copy_asset else f"Campaign for {rule.product_url}"

            any_success = False
            any_failure = False

            for conn_id in connection_ids:
                conn = session.get(PublishConnection, int(conn_id))
                if not conn or not conn.is_active:
                    continue

                try:
                    access_token = decrypt_api_key(
                        conn.access_token, settings.API_KEY_ENCRYPTION_KEY
                    )

                    if conn.platform.value == "FACEBOOK":
                        result = await meta_adapter.publish_to_facebook(
                            page_access_token=access_token,
                            page_id=conn.page_id or "",
                            message=caption,
                            image_url=image_url,
                        )
                    elif conn.platform.value == "INSTAGRAM":
                        if not image_url:
                            continue
                        result = await meta_adapter.publish_to_instagram(
                            page_access_token=access_token,
                            ig_user_id=conn.account_id or "",
                            image_url=image_url,
                            caption=caption,
                        )
                    elif conn.platform.value == "X":
                        result = await x_adapter.publish_tweet(
                            access_token=access_token,
                            text=caption,
                        )
                    elif conn.platform.value == "THREADS":
                        result = await threads_adapter.publish_to_threads(
                            access_token=access_token,
                            user_id=conn.account_id or "",
                            text=caption,
                            image_url=image_url,
                        )
                    else:
                        continue

                    if result.get("success"):
                        any_success = True
                    else:
                        any_failure = True
                except Exception:
                    any_failure = True

            if any_success and not any_failure:
                pub_status = "published"
            elif any_success:
                pub_status = "partial"
            elif any_failure:
                pub_status = "failed"
            else:
                pub_status = "skipped"

            run_log = session.exec(
                select(AutopilotRunLog).where(
                    AutopilotRunLog.rule_id == rule_id,
                    AutopilotRunLog.campaign_id == campaign_id,
                )
            ).first()
            if run_log:
                run_log.publish_status = pub_status
                session.add(run_log)
                session.commit()

            try:
                from app.services.notifications import create_notification as _create_notif

                if pub_status in ("published", "partial"):
                    _create_notif(
                        session, rule.user_id, NotificationType.PUBLISH_COMPLETE,
                        "Auto-publish completed",
                        f"Campaign for {rule.product_url} published ({pub_status})",
                        {"campaign_id": campaign_id, "rule_id": rule_id, "status": pub_status},
                    )
                elif pub_status == "failed":
                    _create_notif(
                        session, rule.user_id, NotificationType.PUBLISH_FAILED,
                        "Auto-publish failed",
                        f"Campaign for {rule.product_url} publish failed",
                        {"campaign_id": campaign_id, "rule_id": rule_id},
                    )
            except Exception:
                pass

    except Exception:
        logger.exception("Auto-publish failed for campaign %s rule %s", campaign_id, rule_id)
    else:
        try:
            from app.api.websocket import send_autopilot_event

            await send_autopilot_event(rule.user_id, "publish_complete", {
                "campaign_id": campaign_id,
                "status": pub_status,
            })
        except Exception:
            pass
