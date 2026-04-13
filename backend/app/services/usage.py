from datetime import datetime, UTC
from typing import Tuple
from sqlmodel import Session
from fastapi import HTTPException, status

from app.models.models import (
    User,
    Subscription,
    UsageTracking,
    CreditUsageLog,
    PlanTier,
    PLAN_LIMITS,
    CREDIT_COSTS,
    utc_now,
)


def get_or_create_subscription(session: Session, user: User) -> Subscription:
    if user.subscription:
        return user.subscription
    subscription = Subscription(user_id=user.id, tier=PlanTier.FREE)
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def get_or_create_usage(session: Session, user: User) -> UsageTracking:
    if user.usage:
        return user.usage
    usage = UsageTracking(user_id=user.id)
    session.add(usage)
    session.commit()
    session.refresh(usage)
    return usage


def check_and_reset_period(
    session: Session, usage: UsageTracking, subscription: Subscription
):
    now = utc_now()
    limits = PLAN_LIMITS.get(subscription.tier, PLAN_LIMITS[PlanTier.FREE])
    allows_rollover = limits.get("credit_rollover", False)

    def _do_reset():
        rollover = 0
        if allows_rollover:
            credits_limit = limits["credits_per_month"]
            bonus = usage.bonus_credits or 0
            rolled = usage.rolled_over_credits or 0
            remaining = (credits_limit + bonus + rolled) - usage.credits_used
            rollover = max(0, remaining)
        usage.reset_period(subscription.current_period_start or now, rollover)
        session.add(usage)
        session.commit()

    if subscription.current_period_end and now > subscription.current_period_end:
        _do_reset()
    else:
        period_start = usage.period_start
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=UTC)
        if (now - period_start).days >= 30:
            _do_reset()


def get_user_limits(
    session: Session, user: User
) -> Tuple[Subscription, UsageTracking, dict]:
    subscription = get_or_create_subscription(session, user)
    usage = get_or_create_usage(session, user)
    check_and_reset_period(session, usage, subscription)
    return subscription, usage, subscription.limits


def _is_byok(session: Session, user: User) -> bool:
    subscription = get_or_create_subscription(session, user)
    return subscription.tier == PlanTier.BYOK


def check_credits(session: Session, user: User, credits_needed: int) -> None:
    if _is_byok(session, user):
        return

    subscription, usage, limits = get_user_limits(session, user)
    credits_limit = limits["credits_per_month"]
    bonus_credits = usage.bonus_credits or 0
    rolled_over = usage.rolled_over_credits or 0
    total_available = credits_limit + bonus_credits + rolled_over
    credits_remaining = total_available - usage.credits_used

    if credits_needed > credits_remaining:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_credits",
                "credits_needed": credits_needed,
                "credits_remaining": credits_remaining,
                "credits_limit": credits_limit,
                "bonus_credits": bonus_credits,
                "rolled_over_credits": rolled_over,
                "tier": subscription.tier.value,
                "message": f"Not enough credits. Need {credits_needed}, have {credits_remaining}. Upgrade or buy credits.",
            },
        )


def check_image_credits(session: Session, user: User, count: int = 1) -> None:
    credits_needed = count * CREDIT_COSTS["image"]
    check_credits(session, user, credits_needed)


def check_video_credits(session: Session, user: User, count: int = 1) -> None:
    credits_needed = count * CREDIT_COSTS["video"]
    check_credits(session, user, credits_needed)


def check_api_access(session: Session, user: User) -> None:
    subscription, _, limits = get_user_limits(session, user)

    if not limits["api_access"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_not_available",
                "resource": "api_access",
                "tier": subscription.tier.value,
                "message": "API access is not available on your plan. Upgrade to Pro or higher.",
            },
        )


def check_byok_access(session: Session, user: User) -> None:
    subscription = get_or_create_subscription(session, user)
    if not subscription.limits.get("byok", False):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_not_available",
                "resource": "byok",
                "tier": subscription.tier.value,
                "message": "Bring Your Own Key requires the BYOK plan. Upgrade to use your own API keys.",
            },
        )


def use_credits(
    session: Session,
    user: User,
    credits: int,
    resource_type: str = None,
    campaign_id: int = None,
) -> None:
    usage = get_or_create_usage(session, user)
    usage.credits_used += credits
    usage.total_credits_used += credits
    if resource_type == "image":
        usage.total_images += credits // CREDIT_COSTS["image"]
    elif resource_type == "video":
        usage.total_videos += credits // CREDIT_COSTS["video"]
    usage.updated_at = utc_now()
    session.add(usage)

    log = CreditUsageLog(
        user_id=user.id,
        resource_type=resource_type or "unknown",
        credits=credits,
        campaign_id=campaign_id,
    )
    session.add(log)
    session.commit()


def use_image_credits(
    session: Session, user: User, count: int = 1, campaign_id: int = None
) -> None:
    credits = count * CREDIT_COSTS["image"]
    use_credits(session, user, credits, "image", campaign_id)


def use_video_credits(
    session: Session, user: User, count: int = 1, campaign_id: int = None
) -> None:
    credits = count * CREDIT_COSTS["video"]
    use_credits(session, user, credits, "video", campaign_id)


def check_repurpose_credits(session: Session, user: User, count: int = 1) -> None:
    credits_needed = count * CREDIT_COSTS["repurpose"]
    check_credits(session, user, credits_needed)


def use_repurpose_credits(session: Session, user: User, count: int = 1) -> None:
    credits = count * CREDIT_COSTS["repurpose"]
    use_credits(session, user, credits, "repurpose")


def check_product_photo_credits(session: Session, user: User, count: int = 1) -> None:
    credits_needed = count * CREDIT_COSTS["product_photo"]
    check_credits(session, user, credits_needed)


def use_product_photo_credits(
    session: Session, user: User, count: int = 1, campaign_id: int = None
) -> None:
    credits = count * CREDIT_COSTS["product_photo"]
    use_credits(session, user, credits, "product_photo", campaign_id)


def check_tts_credits(session: Session, user: User, count: int = 1) -> None:
    credits_needed = count * CREDIT_COSTS["tts"]
    check_credits(session, user, credits_needed)


def use_tts_credits(
    session: Session, user: User, count: int = 1, campaign_id: int = None
) -> None:
    credits = count * CREDIT_COSTS["tts"]
    use_credits(session, user, credits, "tts", campaign_id)


def check_bgm_credits(session: Session, user: User, count: int = 1) -> None:
    """BGM is free (0 credits) but we still track usage."""
    credits_needed = count * CREDIT_COSTS["bgm"]
    if credits_needed > 0:
        check_credits(session, user, credits_needed)


def use_bgm_credits(
    session: Session, user: User, count: int = 1, campaign_id: int = None
) -> None:
    """BGM is free but we log it for tracking."""
    credits = count * CREDIT_COSTS["bgm"]
    if credits > 0:
        use_credits(session, user, credits, "bgm", campaign_id)
