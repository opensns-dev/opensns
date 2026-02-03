from datetime import datetime, UTC, timedelta
import hashlib
import hmac
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session, select, func

from app.core.config import settings
from app.core.auth import get_current_user
from app.db import get_session
from app.models.models import (
    User,
    Subscription,
    UsageTracking,
    CreditUsageLog,
    PlanTier,
    SubscriptionStatus,
    PLAN_LIMITS,
    CREDIT_COSTS,
    CREDIT_PACKS,
    SubscriptionResponse,
    UsageResponse,
    BillingOverview,
    utc_now,
)

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger(__name__)

TIER_TO_PRICE_ID = {
    PlanTier.BASIC: settings.PADDLE_PRICE_ID_BASIC,
    PlanTier.PRO: settings.PADDLE_PRICE_ID_PRO,
    PlanTier.ULTRA: settings.PADDLE_PRICE_ID_ULTRA,
}

PRICE_ID_TO_TIER = {v: k for k, v in TIER_TO_PRICE_ID.items() if v}

PACK_TO_PRICE_ID = {
    "PACK_50": settings.PADDLE_PRICE_ID_CREDITS_50,
    "PACK_150": settings.PADDLE_PRICE_ID_CREDITS_150,
    "PACK_500": settings.PADDLE_PRICE_ID_CREDITS_500,
}

PRICE_ID_TO_PACK = {v: k for k, v in PACK_TO_PRICE_ID.items() if v}


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


@router.get("/overview", response_model=BillingOverview)
async def get_billing_overview(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    subscription = get_or_create_subscription(session, user)
    usage = get_or_create_usage(session, user)
    limits = subscription.limits

    credits_limit = limits["credits_per_month"]
    total_available = credits_limit + (usage.bonus_credits or 0)
    usage_percentage = (
        min(100, int((usage.credits_used / total_available) * 100))
        if total_available > 0
        else 0
    )

    usage_response = UsageResponse(
        period_start=usage.period_start,
        credits_used=usage.credits_used,
        credits_limit=credits_limit,
        bonus_credits=usage.bonus_credits or 0,
    )

    return BillingOverview(
        subscription=SubscriptionResponse(
            tier=subscription.tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            limits=limits,
        ),
        usage=usage_response,
        credit_costs=CREDIT_COSTS,
        usage_percentage=usage_percentage,
    )


@router.get("/plans")
async def get_available_plans():
    return {
        tier.value: {
            "name": tier.value.capitalize(),
            "price_monthly": limits["price_monthly"],
            "price_display": f"${limits['price_monthly'] / 100:.0f}/mo"
            if limits["price_monthly"] > 0
            else "Free",
            "paddle_price_id": TIER_TO_PRICE_ID.get(tier),
            **{k: v for k, v in limits.items() if k != "price_monthly"},
        }
        for tier, limits in PLAN_LIMITS.items()
    }


@router.get("/credit-packs")
async def get_credit_packs():
    return {
        pack_id: {
            "id": pack_id,
            "paddle_price_id": PACK_TO_PRICE_ID.get(pack_id),
            **pack_info,
        }
        for pack_id, pack_info in CREDIT_PACKS.items()
    }


@router.get("/paddle-config")
async def get_paddle_config(user: User = Depends(get_current_user)):
    if not settings.PADDLE_API_KEY:
        raise HTTPException(status_code=503, detail="Paddle not configured")

    return {
        "environment": settings.PADDLE_ENVIRONMENT,
        "customer_email": user.email,
    }


@router.get("/analytics")
async def get_usage_analytics(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    start_date = utc_now() - timedelta(days=days)

    logs = session.exec(
        select(CreditUsageLog)
        .where(CreditUsageLog.user_id == user.id)
        .where(CreditUsageLog.date >= start_date)
        .order_by(CreditUsageLog.date)
    ).all()

    daily_usage = {}
    by_type = {"image": 0, "video": 0}

    for log in logs:
        date_str = log.date.strftime("%Y-%m-%d")
        if date_str not in daily_usage:
            daily_usage[date_str] = {
                "date": date_str,
                "credits": 0,
                "image": 0,
                "video": 0,
            }
        daily_usage[date_str]["credits"] += log.credits
        daily_usage[date_str][log.resource_type] += log.credits
        if log.resource_type in by_type:
            by_type[log.resource_type] += log.credits

    total_credits = sum(log.credits for log in logs)
    usage = get_or_create_usage(session, user)

    return {
        "period_days": days,
        "total_credits": total_credits,
        "by_type": by_type,
        "daily": sorted(daily_usage.values(), key=lambda x: x["date"]),
        "lifetime": {
            "total_credits": usage.total_credits_used,
            "total_images": usage.total_images,
            "total_videos": usage.total_videos,
        },
    }


def verify_paddle_signature(request_body: bytes, signature: str) -> bool:
    if not settings.PADDLE_WEBHOOK_SECRET:
        return False

    expected = hmac.new(
        settings.PADDLE_WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@router.post("/webhook")
async def paddle_webhook(request: Request, session: Session = Depends(get_session)):
    if not settings.PADDLE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    payload = await request.body()
    signature = request.headers.get("Paddle-Signature", "")

    ts_part = ""
    h1_part = ""
    for part in signature.split(";"):
        if part.startswith("ts="):
            ts_part = part[3:]
        elif part.startswith("h1="):
            h1_part = part[3:]

    if not ts_part or not h1_part:
        raise HTTPException(status_code=400, detail="Invalid signature format")

    signed_payload = f"{ts_part}:{payload.decode()}"
    expected = hmac.new(
        settings.PADDLE_WEBHOOK_SECRET.encode(),
        signed_payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(h1_part, expected):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        event = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("event_type", "")
    data = event.get("data", {})

    logger.info(f"Paddle webhook received: {event_type}")

    if event_type == "subscription.created":
        handle_subscription_created(session, data)
    elif event_type == "subscription.updated":
        handle_subscription_updated(session, data)
    elif event_type == "subscription.canceled":
        handle_subscription_canceled(session, data)
    elif event_type == "transaction.completed":
        handle_transaction_completed(session, data)

    return {"status": "ok"}


def get_user_from_custom_data(session: Session, custom_data: dict) -> Optional[User]:
    user_id = custom_data.get("user_id")
    if not user_id:
        return None
    return session.query(User).filter(User.id == int(user_id)).first()


def handle_subscription_created(session: Session, data: dict):
    custom_data = data.get("custom_data", {})
    user = get_user_from_custom_data(session, custom_data)
    if not user:
        logger.warning(f"Subscription created but no user found: {custom_data}")
        return

    subscription = get_or_create_subscription(session, user)

    items = data.get("items", [])
    if items:
        price_id = items[0].get("price", {}).get("id")
        tier = PRICE_ID_TO_TIER.get(price_id, PlanTier.BASIC)
        subscription.tier = tier
        subscription.paddle_price_id = price_id

    subscription.paddle_subscription_id = data.get("id")
    subscription.paddle_customer_id = data.get("customer_id")
    subscription.status = SubscriptionStatus.ACTIVE

    billing_cycle = data.get("current_billing_period", {})
    if billing_cycle:
        subscription.current_period_start = datetime.fromisoformat(
            billing_cycle.get("starts_at", "").replace("Z", "+00:00")
        )
        subscription.current_period_end = datetime.fromisoformat(
            billing_cycle.get("ends_at", "").replace("Z", "+00:00")
        )

    subscription.updated_at = utc_now()
    session.add(subscription)
    session.commit()

    logger.info(f"Subscription created for user {user.id}: {subscription.tier}")


def handle_subscription_updated(session: Session, data: dict):
    paddle_sub_id = data.get("id")
    subscription = (
        session.query(Subscription)
        .filter(Subscription.paddle_subscription_id == paddle_sub_id)
        .first()
    )

    if not subscription:
        logger.warning(f"Subscription not found for update: {paddle_sub_id}")
        return

    items = data.get("items", [])
    if items:
        price_id = items[0].get("price", {}).get("id")
        tier = PRICE_ID_TO_TIER.get(price_id)
        if tier:
            subscription.tier = tier
            subscription.paddle_price_id = price_id

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "trialing": SubscriptionStatus.TRIALING,
    }
    paddle_status = data.get("status", "active")
    subscription.status = status_map.get(paddle_status, SubscriptionStatus.ACTIVE)

    billing_cycle = data.get("current_billing_period", {})
    if billing_cycle:
        subscription.current_period_start = datetime.fromisoformat(
            billing_cycle.get("starts_at", "").replace("Z", "+00:00")
        )
        subscription.current_period_end = datetime.fromisoformat(
            billing_cycle.get("ends_at", "").replace("Z", "+00:00")
        )

    subscription.cancel_at_period_end = (
        data.get("scheduled_change", {}).get("action") == "cancel"
    )
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()

    logger.info(f"Subscription updated: {paddle_sub_id}")


def handle_subscription_canceled(session: Session, data: dict):
    paddle_sub_id = data.get("id")
    subscription = (
        session.query(Subscription)
        .filter(Subscription.paddle_subscription_id == paddle_sub_id)
        .first()
    )

    if not subscription:
        return

    subscription.tier = PlanTier.FREE
    subscription.status = SubscriptionStatus.CANCELED
    subscription.paddle_subscription_id = None
    subscription.paddle_price_id = None
    subscription.current_period_start = None
    subscription.current_period_end = None
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()

    logger.info(f"Subscription canceled: {paddle_sub_id}")


def handle_transaction_completed(session: Session, data: dict):
    custom_data = data.get("custom_data", {})

    if custom_data.get("type") != "credit_topup":
        return

    user_id = custom_data.get("user_id")
    credits = custom_data.get("credits")

    if not user_id or not credits:
        return

    usage = (
        session.query(UsageTracking)
        .filter(UsageTracking.user_id == int(user_id))
        .first()
    )

    if not usage:
        usage = UsageTracking(user_id=int(user_id), bonus_credits=int(credits))
        session.add(usage)
    else:
        usage.bonus_credits = (usage.bonus_credits or 0) + int(credits)
        session.add(usage)

    session.commit()

    logger.info(f"Credit top-up for user {user_id}: +{credits} credits")
