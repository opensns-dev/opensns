"""
Tests for subscription and billing functionality (credit-based system).
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.models import (
    User,
    Subscription,
    UsageTracking,
    PlanTier,
    SubscriptionStatus,
    PLAN_LIMITS,
    CREDIT_COSTS,
    CREDIT_PACKS,
)
from app.services.usage import (
    get_or_create_subscription,
    get_or_create_usage,
    check_credits,
    check_image_credits,
    check_video_credits,
    use_credits,
    use_image_credits,
    use_video_credits,
)
from fastapi import HTTPException


class TestCreditCosts:
    def test_image_credit_cost(self):
        assert CREDIT_COSTS["image"] == 1

    def test_video_credit_cost(self):
        assert CREDIT_COSTS["video"] == 12

    def test_product_photo_credit_cost(self):
        assert CREDIT_COSTS["product_photo"] == 3


class TestPlanCredits:
    def test_free_tier_credits(self):
        limits = PLAN_LIMITS[PlanTier.FREE]
        assert limits["credits_per_month"] == 50

    def test_basic_tier_credits(self):
        limits = PLAN_LIMITS[PlanTier.BASIC]
        assert limits["credits_per_month"] == 150

    def test_pro_tier_credits(self):
        limits = PLAN_LIMITS[PlanTier.PRO]
        assert limits["credits_per_month"] == 500

    def test_ultra_tier_credits(self):
        limits = PLAN_LIMITS[PlanTier.ULTRA]
        assert limits["credits_per_month"] == 1200


class TestCreditPricing:
    def test_byok_tier_unlimited_credits(self):
        limits = PLAN_LIMITS[PlanTier.BYOK]
        assert limits["credits_per_month"] == -1
        assert limits["byok"] is True

    def test_higher_tiers_better_value(self):
        basic_per_credit = 900 / PLAN_LIMITS[PlanTier.BASIC]["credits_per_month"]
        pro_per_credit = 2900 / PLAN_LIMITS[PlanTier.PRO]["credits_per_month"]
        ultra_per_credit = 5900 / PLAN_LIMITS[PlanTier.ULTRA]["credits_per_month"]

        assert pro_per_credit < basic_per_credit
        assert ultra_per_credit < pro_per_credit


class TestSubscriptionCreation:
    def test_get_or_create_subscription_creates_free(
        self, session: Session, test_user: User
    ):
        subscription = get_or_create_subscription(session, test_user)
        assert subscription is not None
        assert subscription.tier == PlanTier.FREE
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.user_id == test_user.id

    def test_get_or_create_subscription_returns_existing(
        self, session: Session, test_user: User
    ):
        sub1 = get_or_create_subscription(session, test_user)
        sub1.tier = PlanTier.PRO
        session.add(sub1)
        session.commit()

        sub2 = get_or_create_subscription(session, test_user)
        assert sub2.id == sub1.id
        assert sub2.tier == PlanTier.PRO


class TestCreditUsage:
    def test_get_or_create_usage(self, session: Session, test_user: User):
        usage = get_or_create_usage(session, test_user)
        assert usage is not None
        assert usage.credits_used == 0

    def test_use_image_credits(self, session: Session, test_user: User):
        get_or_create_usage(session, test_user)
        use_image_credits(session, test_user, 3)

        session.refresh(test_user)
        usage = get_or_create_usage(session, test_user)
        assert usage.credits_used == 3
        assert usage.total_images == 3

    def test_use_video_credits(self, session: Session, test_user: User):
        get_or_create_usage(session, test_user)
        use_video_credits(session, test_user, 1)

        session.refresh(test_user)
        usage = get_or_create_usage(session, test_user)
        assert usage.credits_used == 12
        assert usage.total_videos == 1


class TestCreditChecks:
    def test_check_credits_passes_when_available(
        self, session: Session, test_user: User
    ):
        get_or_create_subscription(session, test_user)
        get_or_create_usage(session, test_user)
        check_credits(session, test_user, 5)

    def test_check_credits_fails_when_exceeded(self, session: Session, test_user: User):
        get_or_create_subscription(session, test_user)
        usage = get_or_create_usage(session, test_user)
        usage.credits_used = 48
        session.add(usage)
        session.commit()

        with pytest.raises(HTTPException) as exc_info:
            check_credits(session, test_user, 5)
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "insufficient_credits"

    def test_check_image_credits_uses_correct_cost(
        self, session: Session, test_user: User
    ):
        get_or_create_subscription(session, test_user)
        usage = get_or_create_usage(session, test_user)
        usage.credits_used = 49
        session.add(usage)
        session.commit()

        check_image_credits(session, test_user, 1)

        with pytest.raises(HTTPException):
            check_image_credits(session, test_user, 2)

    def test_check_video_credits_uses_correct_cost(
        self, session: Session, test_user: User
    ):
        get_or_create_subscription(session, test_user)
        usage = get_or_create_usage(session, test_user)
        usage.credits_used = 40
        session.add(usage)
        session.commit()

        with pytest.raises(HTTPException):
            check_video_credits(session, test_user, 1)


class TestBillingAPI:
    def test_get_billing_overview(
        self, client: TestClient, auth_headers: dict, test_user: User
    ):
        response = client.get("/billing/overview", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "subscription" in data
        assert "usage" in data
        assert "credit_costs" in data
        assert "usage_percentage" in data
        assert data["subscription"]["tier"] == "FREE"
        assert data["credit_costs"]["image"] == 1
        assert data["credit_costs"]["video"] == 12

    def test_get_plans(self, client: TestClient, auth_headers: dict):
        response = client.get("/billing/plans", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "FREE" in data
        assert "BASIC" in data
        assert "PRO" in data
        assert "ULTRA" in data
        assert "BYOK" in data
        assert data["BASIC"]["credits_per_month"] == 150
        assert data["PRO"]["credits_per_month"] == 500
        assert data["ULTRA"]["credits_per_month"] == 1200
        assert data["BYOK"]["credits_per_month"] == -1
        assert "variant_id" in data["BASIC"]

    def test_ls_config_requires_api_key(self, client: TestClient, auth_headers: dict):
        response = client.get("/billing/ls-config", headers=auth_headers)
        assert response.status_code == 503


class TestCampaignCreditIntegration:
    def test_campaign_creation_checks_credits(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        usage = get_or_create_usage(session, test_user)
        usage.credits_used = 48
        session.add(usage)
        session.commit()

        response = client.post(
            "/campaigns/",
            headers=auth_headers,
            json={
                "title": "Test Campaign",
                "product_url": "https://example.com/product",
            },
        )
        assert response.status_code == 402
        assert response.json()["detail"]["error"] == "insufficient_credits"


class TestCreditPacks:
    def test_get_credit_packs(self, client: TestClient, auth_headers: dict):
        response = client.get("/billing/credit-packs", headers=auth_headers)
        assert response.status_code == 200
        packs = response.json()
        assert "PACK_50" in packs
        assert "PACK_150" in packs
        assert "PACK_500" in packs
        assert packs["PACK_50"]["credits"] == 50
        assert packs["PACK_150"]["credits"] == 150
        assert packs["PACK_500"]["credits"] == 500
        assert "variant_id" in packs["PACK_50"]


class TestBonusCredits:
    def test_bonus_credits_included_in_overview(
        self, client: TestClient, auth_headers: dict, session: Session, test_user: User
    ):
        usage = get_or_create_usage(session, test_user)
        usage.bonus_credits = 100
        session.add(usage)
        session.commit()

        response = client.get("/billing/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["usage"]["bonus_credits"] == 100

    def test_bonus_credits_extend_available_credits(
        self, session: Session, test_user: User
    ):
        usage = get_or_create_usage(session, test_user)
        usage.bonus_credits = 50
        usage.credits_used = 45
        session.add(usage)
        session.commit()

        check_credits(session, test_user, 55)

    def test_bonus_credits_insufficient_still_fails(
        self, session: Session, test_user: User
    ):
        usage = get_or_create_usage(session, test_user)
        usage.bonus_credits = 10
        usage.credits_used = 55
        session.add(usage)
        session.commit()

        with pytest.raises(HTTPException) as exc_info:
            check_credits(session, test_user, 10)
        assert exc_info.value.status_code == 402
