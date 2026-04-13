from datetime import datetime, UTC, timedelta
import hashlib
import hmac
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlmodel import Session, select
import httpx

from app.core.config import settings
from app.core.auth import get_current_user
from app.core.rate_limit import limiter
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

TIER_TO_VARIANT_ID = {
    PlanTier.BASIC: settings.LEMONSQUEEZY_VARIANT_ID_BASIC,
    PlanTier.BYOK: settings.LEMONSQUEEZY_VARIANT_ID_BYOK,
    PlanTier.PRO: settings.LEMONSQUEEZY_VARIANT_ID_PRO,
    PlanTier.ULTRA: settings.LEMONSQUEEZY_VARIANT_ID_ULTRA,
}

VARIANT_ID_TO_TIER = {v: k for k, v in TIER_TO_VARIANT_ID.items() if v}

PACK_TO_VARIANT_ID = {
    "PACK_50": settings.LEMONSQUEEZY_VARIANT_ID_CREDITS_50,
    "PACK_150": settings.LEMONSQUEEZY_VARIANT_ID_CREDITS_150,
    "PACK_500": settings.LEMONSQUEEZY_VARIANT_ID_CREDITS_500,
}

VARIANT_ID_TO_PACK = {v: k for k, v in PACK_TO_VARIANT_ID.items() if v}


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
@limiter.limit("60/minute")
async def get_billing_overview(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    subscription = get_or_create_subscription(session, user)
    usage = get_or_create_usage(session, user)
    limits = subscription.limits

    credits_limit = limits["credits_per_month"]
    if credits_limit == -1:
        usage_percentage = 0
    else:
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
@limiter.limit("60/minute")
async def get_available_plans(request: Request):
    return {
        tier.value: {
            "name": tier.value.capitalize(),
            "price_monthly": limits["price_monthly"],
            "price_display": f"${limits['price_monthly'] / 100:.0f}/mo"
            if limits["price_monthly"] > 0
            else "Free",
            "variant_id": TIER_TO_VARIANT_ID.get(tier),
            **{k: v for k, v in limits.items() if k != "price_monthly"},
        }
        for tier, limits in PLAN_LIMITS.items()
    }


@router.get("/credit-packs")
@limiter.limit("60/minute")
async def get_credit_packs(request: Request):
    return {
        pack_id: {
            "id": pack_id,
            "variant_id": PACK_TO_VARIANT_ID.get(pack_id),
            **pack_info,
        }
        for pack_id, pack_info in CREDIT_PACKS.items()
    }


@router.get("/ls-config")
@limiter.limit("60/minute")
async def get_ls_config(request: Request, user: User = Depends(get_current_user)):
    if not settings.LEMONSQUEEZY_API_KEY:
        raise HTTPException(status_code=503, detail="LemonSqueezy not configured")

    return {
        "store_id": settings.LEMONSQUEEZY_STORE_ID,
        "customer_email": user.email,
    }


class CheckoutRequest(BaseModel):
    variant_id: str
    checkout_type: str = "subscription"
    custom_data: dict = {}


@router.post("/create-checkout")
@limiter.limit("30/minute")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
):
    if not settings.LEMONSQUEEZY_API_KEY:
        raise HTTPException(status_code=503, detail="LemonSqueezy not configured")

    if body.checkout_type not in ("subscription", "credit_topup"):
        raise HTTPException(status_code=400, detail="Invalid checkout_type")

    custom = {
        "user_id": str(user.id),
        "type": body.checkout_type,
        **body.custom_data,
    }

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user.email,
                    "custom": custom,
                },
                "checkout_options": {
                    "embed": True,
                },
                "product_options": {
                    "enabled_variants": [int(body.variant_id)],
                },
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": settings.LEMONSQUEEZY_STORE_ID,
                    }
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": body.variant_id,
                    }
                },
            },
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers={
                "Authorization": f"Bearer {settings.LEMONSQUEEZY_API_KEY}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            },
            json=payload,
            timeout=15.0,
        )

    if response.status_code != 201:
        logger.error(f"LemonSqueezy checkout creation failed: {response.text}")
        raise HTTPException(status_code=502, detail="Failed to create checkout")

    data = response.json()
    checkout_url = data["data"]["attributes"]["url"]

    return {"url": checkout_url}


@router.get("/analytics")
@limiter.limit("60/minute")
async def get_usage_analytics(
    request: Request,
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


def verify_lemonsqueezy_signature(request_body: bytes, signature: str) -> bool:
    if not settings.LEMONSQUEEZY_WEBHOOK_SECRET:
        return False

    expected = hmac.new(
        settings.LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@router.post("/webhook")
@limiter.limit("30/minute")
async def lemonsqueezy_webhook(
    request: Request, session: Session = Depends(get_session)
):
    if not settings.LEMONSQUEEZY_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    payload = await request.body()
    signature = request.headers.get("X-Signature", "")

    if not verify_lemonsqueezy_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        event = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_name = request.headers.get("X-Event-Name", "")
    data = event.get("data", {})
    meta = event.get("meta", {})

    logger.info(f"LemonSqueezy webhook received: {event_name}")

    if event_name == "subscription_created":
        handle_subscription_created(session, data, meta)
    elif event_name == "subscription_updated":
        handle_subscription_updated(session, data)
    elif event_name == "subscription_cancelled":
        handle_subscription_cancelled(session, data)
    elif event_name == "subscription_expired":
        handle_subscription_expired(session, data)
    elif event_name == "order_created":
        handle_order_created(session, data, meta)

    return {"status": "ok"}


def get_user_from_custom_data(session: Session, custom_data: dict) -> Optional[User]:
    user_id = custom_data.get("user_id")
    if not user_id:
        return None
    return session.exec(select(User).where(User.id == int(user_id))).first()


def handle_subscription_created(session: Session, data: dict, meta: dict):
    attributes = data.get("attributes", {})
    custom_data = meta.get("custom_data", {})

    user = get_user_from_custom_data(session, custom_data)
    if not user:
        logger.warning(f"Subscription created but no user found: {custom_data}")
        return

    subscription = get_or_create_subscription(session, user)

    variant_id = str(attributes.get("variant_id", ""))
    tier = VARIANT_ID_TO_TIER.get(variant_id, PlanTier.BASIC)
    subscription.tier = tier
    subscription.ls_variant_id = variant_id

    subscription.ls_subscription_id = str(data.get("id", ""))
    subscription.ls_customer_id = str(attributes.get("customer_id", ""))
    subscription.status = SubscriptionStatus.ACTIVE

    renews_at = attributes.get("renews_at")
    if renews_at:
        subscription.current_period_end = datetime.fromisoformat(
            renews_at.replace("Z", "+00:00")
        )

    created_at = attributes.get("created_at")
    if created_at:
        subscription.current_period_start = datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        )

    subscription.updated_at = utc_now()
    session.add(subscription)
    session.commit()

    logger.info(f"Subscription created for user {user.id}: {subscription.tier}")


def handle_subscription_updated(session: Session, data: dict):
    attributes = data.get("attributes", {})
    ls_sub_id = str(data.get("id", ""))

    subscription = session.exec(
        select(Subscription).where(Subscription.ls_subscription_id == ls_sub_id)
    ).first()

    if not subscription:
        logger.warning(f"Subscription not found for update: {ls_sub_id}")
        return

    variant_id = str(attributes.get("variant_id", ""))
    if variant_id and variant_id in VARIANT_ID_TO_TIER:
        tier = VARIANT_ID_TO_TIER.get(variant_id)
        if tier:
            subscription.tier = tier
            subscription.ls_variant_id = variant_id

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "cancelled": SubscriptionStatus.CANCELED,
        "expired": SubscriptionStatus.CANCELED,
        "paused": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.PAST_DUE,
        "on_trial": SubscriptionStatus.TRIALING,
    }
    ls_status = attributes.get("status", "active")
    subscription.status = status_map.get(ls_status, SubscriptionStatus.ACTIVE)

    renews_at = attributes.get("renews_at")
    if renews_at:
        subscription.current_period_end = datetime.fromisoformat(
            renews_at.replace("Z", "+00:00")
        )

    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()

    logger.info(f"Subscription updated: {ls_sub_id}")


def handle_subscription_cancelled(session: Session, data: dict):
    attributes = data.get("attributes", {})
    ls_sub_id = str(data.get("id", ""))

    subscription = session.exec(
        select(Subscription).where(Subscription.ls_subscription_id == ls_sub_id)
    ).first()

    if not subscription:
        return

    subscription.tier = PlanTier.FREE
    subscription.status = SubscriptionStatus.CANCELED
    subscription.ls_subscription_id = None
    subscription.ls_variant_id = None
    subscription.current_period_start = None
    subscription.current_period_end = None
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()

    logger.info(f"Subscription cancelled: {ls_sub_id}")


def handle_subscription_expired(session: Session, data: dict):
    handle_subscription_cancelled(session, data)


def handle_order_created(session: Session, data: dict, meta: dict):
    attributes = data.get("attributes", {})
    custom_data = meta.get("custom_data", {})

    if custom_data.get("type") != "credit_topup":
        return

    user_id = custom_data.get("user_id")

    variant_id = str(attributes.get("variant_id", ""))
    pack_id = VARIANT_ID_TO_PACK.get(variant_id)

    if not pack_id or not user_id:
        return

    from app.models.models import CREDIT_PACKS

    pack_info = CREDIT_PACKS.get(pack_id, {})
    credits = pack_info.get("credits", 0)

    if not credits:
        return

    usage = session.exec(
        select(UsageTracking).where(UsageTracking.user_id == int(user_id))
    ).first()

    if not usage:
        usage = UsageTracking(user_id=int(user_id), bonus_credits=credits)
        session.add(usage)
    else:
        usage.bonus_credits = (usage.bonus_credits or 0) + credits
        session.add(usage)

    session.commit()

    logger.info(f"Credit top-up for user {user_id}: +{credits} credits")
