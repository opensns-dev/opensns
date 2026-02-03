from datetime import datetime, UTC, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session, select, func
import stripe

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

TIER_TO_PRICE_ID = {
    PlanTier.BASIC: settings.STRIPE_PRICE_ID_BASIC,
    PlanTier.PRO: settings.STRIPE_PRICE_ID_PRO,
    PlanTier.ULTRA: settings.STRIPE_PRICE_ID_ULTRA,
}

PACK_TO_PRICE_ID = {
    "PACK_50": settings.STRIPE_PRICE_ID_CREDITS_50,
    "PACK_150": settings.STRIPE_PRICE_ID_CREDITS_150,
    "PACK_500": settings.STRIPE_PRICE_ID_CREDITS_500,
}


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
            **{k: v for k, v in limits.items() if k != "price_monthly"},
        }
        for tier, limits in PLAN_LIMITS.items()
    }


@router.get("/credit-packs")
async def get_credit_packs():
    return {
        pack_id: {
            "id": pack_id,
            **pack_info,
        }
        for pack_id, pack_info in CREDIT_PACKS.items()
    }


@router.post("/topup")
async def create_topup_checkout(
    pack_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if pack_id not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail=f"Invalid pack: {pack_id}")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    price_id = PACK_TO_PRICE_ID.get(pack_id)

    if not price_id:
        raise HTTPException(
            status_code=400, detail=f"No price configured for {pack_id}"
        )

    subscription = get_or_create_subscription(session, user)

    if not subscription.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email, metadata={"user_id": str(user.id)}
        )
        subscription.stripe_customer_id = customer.id
        session.add(subscription)
        session.commit()

    pack_info = CREDIT_PACKS[pack_id]
    checkout_session = stripe.checkout.Session.create(
        customer=subscription.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="payment",
        success_url=f"{settings.FRONTEND_URL}/settings/billing?topup=success",
        cancel_url=f"{settings.FRONTEND_URL}/settings/billing?topup=canceled",
        metadata={
            "user_id": str(user.id),
            "pack_id": pack_id,
            "credits": str(pack_info["credits"]),
        },
    )

    return {"checkout_url": checkout_session.url}


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


@router.post("/checkout")
async def create_checkout_session(
    tier: PlanTier,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if tier == PlanTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot checkout for free tier")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    price_id = TIER_TO_PRICE_ID.get(tier)

    if not price_id:
        raise HTTPException(
            status_code=400, detail=f"No price configured for {tier.value}"
        )

    subscription = get_or_create_subscription(session, user)

    if not subscription.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email, metadata={"user_id": str(user.id)}
        )
        subscription.stripe_customer_id = customer.id
        session.add(subscription)
        session.commit()

    checkout_session = stripe.checkout.Session.create(
        customer=subscription.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.FRONTEND_URL}/settings/billing?success=true",
        cancel_url=f"{settings.FRONTEND_URL}/settings/billing?canceled=true",
        metadata={"user_id": str(user.id), "tier": tier.value},
    )

    return {"checkout_url": checkout_session.url}


@router.post("/portal")
async def create_portal_session(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    subscription = get_or_create_subscription(session, user)

    if not subscription.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    portal_session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/settings/billing",
    )

    return {"portal_url": portal_session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        handle_checkout_completed(session, event["data"]["object"])
    elif event["type"] == "customer.subscription.updated":
        handle_subscription_updated(session, event["data"]["object"])
    elif event["type"] == "customer.subscription.deleted":
        handle_subscription_deleted(session, event["data"]["object"])
    elif event["type"] == "invoice.payment_failed":
        handle_payment_failed(session, event["data"]["object"])

    return {"status": "ok"}


def handle_checkout_completed(session: Session, checkout_data: dict):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user_id = checkout_data.get("metadata", {}).get("user_id")
    tier_value = checkout_data.get("metadata", {}).get("tier")
    pack_id = checkout_data.get("metadata", {}).get("pack_id")
    credits_to_add = checkout_data.get("metadata", {}).get("credits")

    if not user_id:
        return

    if pack_id and credits_to_add:
        handle_credit_topup(session, int(user_id), int(credits_to_add))
        return

    if not tier_value:
        return

    subscription = (
        session.query(Subscription).filter(Subscription.user_id == int(user_id)).first()
    )

    if not subscription:
        return

    stripe_sub = stripe.Subscription.retrieve(checkout_data["subscription"])

    subscription.tier = PlanTier(tier_value)
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.stripe_subscription_id = stripe_sub.id
    subscription.stripe_price_id = stripe_sub["items"]["data"][0]["price"]["id"]
    subscription.current_period_start = datetime.fromtimestamp(
        stripe_sub.current_period_start, tz=UTC
    )
    subscription.current_period_end = datetime.fromtimestamp(
        stripe_sub.current_period_end, tz=UTC
    )
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()


def handle_credit_topup(session: Session, user_id: int, credits: int):
    usage = (
        session.query(UsageTracking).filter(UsageTracking.user_id == user_id).first()
    )

    if not usage:
        usage = UsageTracking(user_id=user_id, bonus_credits=credits)
        session.add(usage)
    else:
        usage.bonus_credits = (usage.bonus_credits or 0) + credits
        session.add(usage)

    session.commit()


def handle_subscription_updated(session: Session, sub_data: dict):
    subscription = (
        session.query(Subscription)
        .filter(Subscription.stripe_subscription_id == sub_data["id"])
        .first()
    )

    if not subscription:
        return

    subscription.current_period_start = datetime.fromtimestamp(
        sub_data["current_period_start"], tz=UTC
    )
    subscription.current_period_end = datetime.fromtimestamp(
        sub_data["current_period_end"], tz=UTC
    )
    subscription.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "trialing": SubscriptionStatus.TRIALING,
    }
    subscription.status = status_map.get(sub_data["status"], SubscriptionStatus.ACTIVE)
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()


def handle_subscription_deleted(session: Session, sub_data: dict):
    subscription = (
        session.query(Subscription)
        .filter(Subscription.stripe_subscription_id == sub_data["id"])
        .first()
    )

    if not subscription:
        return

    subscription.tier = PlanTier.FREE
    subscription.status = SubscriptionStatus.CANCELED
    subscription.stripe_subscription_id = None
    subscription.stripe_price_id = None
    subscription.current_period_start = None
    subscription.current_period_end = None
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()


def handle_payment_failed(session: Session, invoice_data: dict):
    customer_id = invoice_data.get("customer")
    if not customer_id:
        return

    subscription = (
        session.query(Subscription)
        .filter(Subscription.stripe_customer_id == customer_id)
        .first()
    )

    if not subscription:
        return

    subscription.status = SubscriptionStatus.PAST_DUE
    subscription.updated_at = utc_now()

    session.add(subscription)
    session.commit()
