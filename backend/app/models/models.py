from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    return datetime.now(UTC)


# ============ Subscription/Plan Enums ============


class PlanTier(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    ULTRA = "ULTRA"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    PAST_DUE = "PAST_DUE"
    TRIALING = "TRIALING"


class CampaignStatus(str, Enum):
    PENDING = "PENDING"
    RESEARCHING = "RESEARCHING"
    GENERATING = "GENERATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============ User Models ============


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None, index=True)
    verification_token_expires: Optional[datetime] = Field(default=None)
    auth_provider: str = Field(default="email")
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)

    campaigns: List["Campaign"] = Relationship(back_populates="user")
    settings: Optional["UserSettings"] = Relationship(back_populates="user")
    subscription: Optional["Subscription"] = Relationship(back_populates="user")
    usage: Optional["UsageTracking"] = Relationship(back_populates="user")


class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_verified: bool
    auth_provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ============ User Settings Models ============


class UserSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    openai_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None

    default_llm_engine: str = "openai"
    default_image_engine: str = "fal"
    default_video_engine: str = "fal-video"

    ollama_url: Optional[str] = None
    comfyui_url: Optional[str] = None

    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="settings")


class UserSettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None
    default_llm_engine: Optional[str] = None
    default_image_engine: Optional[str] = None
    default_video_engine: Optional[str] = None
    ollama_url: Optional[str] = None
    comfyui_url: Optional[str] = None


class UserSettingsResponse(BaseModel):
    default_llm_engine: str
    default_image_engine: str
    default_video_engine: str
    ollama_url: Optional[str]
    comfyui_url: Optional[str]
    has_openai_key: bool
    has_fal_key: bool
    has_firecrawl_key: bool

    model_config = ConfigDict(from_attributes=True)


# ============ Campaign Models ============


class CampaignBase(SQLModel):
    title: str
    product_url: str
    description: Optional[str] = None


class Campaign(CampaignBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    status: CampaignStatus = Field(default=CampaignStatus.PENDING)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="campaigns")
    assets: List["Asset"] = Relationship(back_populates="campaign")
    agents: List["AgentLog"] = Relationship(back_populates="campaign")


class CampaignCreate(CampaignBase):
    pass


class AssetType(str, Enum):
    COPY = "COPY"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    type: AssetType
    content: str  # Text copy or image URL
    asset_metadata: str = Field(
        default="{}"
    )  # JSON string (renamed from 'metadata' which is reserved)
    created_at: datetime = Field(default_factory=utc_now)

    campaign: Campaign = Relationship(back_populates="assets")


class AgentLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    agent_name: str
    message: str
    level: str = "INFO"
    created_at: datetime = Field(default_factory=utc_now)

    campaign: Campaign = Relationship(back_populates="agents")


# ============ Subscription/Billing Models ============


# Credit costs per action
CREDIT_COSTS = {
    "image": 1,
    "video": 12,
}

CREDIT_PACKS = {
    "PACK_50": {"credits": 50, "price_cents": 499, "price_display": "$4.99"},
    "PACK_150": {"credits": 150, "price_cents": 1299, "price_display": "$12.99"},
    "PACK_500": {"credits": 500, "price_cents": 3999, "price_display": "$39.99"},
}

# Plan limits configuration (not a database table)
PLAN_LIMITS = {
    PlanTier.FREE: {
        "price_monthly": 0,
        "credits_per_month": 20,
        "team_members": 1,
        "api_access": False,
        "white_label": False,
        "competitor_research": False,
        "priority_queue": False,
    },
    PlanTier.BASIC: {
        "price_monthly": 899,  # $8.99 in cents
        "credits_per_month": 145,
        "team_members": 1,
        "api_access": False,
        "white_label": False,
        "competitor_research": True,
        "priority_queue": False,
    },
    PlanTier.PRO: {
        "price_monthly": 2899,  # $28.99 in cents
        "credits_per_month": 545,
        "team_members": 3,
        "api_access": True,
        "white_label": False,
        "competitor_research": True,
        "priority_queue": True,
    },
    PlanTier.ULTRA: {
        "price_monthly": 9899,  # $98.99 in cents
        "credits_per_month": 1980,
        "team_members": 20,
        "api_access": True,
        "white_label": True,
        "competitor_research": True,
        "priority_queue": True,
    },
}


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    tier: PlanTier = Field(default=PlanTier.FREE)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE)

    # Stripe integration
    stripe_customer_id: Optional[str] = Field(default=None, index=True)
    stripe_subscription_id: Optional[str] = Field(default=None, index=True)
    stripe_price_id: Optional[str] = None

    # Billing cycle
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = Field(default=False)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional["User"] = Relationship(back_populates="subscription")

    @property
    def limits(self) -> dict:
        """Get the limits for this subscription's tier."""
        return PLAN_LIMITS.get(self.tier, PLAN_LIMITS[PlanTier.FREE])

    @property
    def is_paid(self) -> bool:
        return self.tier != PlanTier.FREE


class UsageTracking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    period_start: datetime = Field(default_factory=utc_now)
    credits_used: int = Field(default=0)
    bonus_credits: int = Field(default=0)

    total_credits_used: int = Field(default=0)
    total_images: int = Field(default=0)
    total_videos: int = Field(default=0)

    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional["User"] = Relationship(back_populates="usage")

    def reset_period(self, new_period_start: datetime = None):
        self.period_start = new_period_start or utc_now()
        self.credits_used = 0
        self.updated_at = utc_now()


class CreditUsageLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: datetime = Field(default_factory=utc_now, index=True)
    resource_type: str = Field(default="image")
    credits: int = Field(default=1)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaign.id")

    user: Optional["User"] = Relationship()


# ============ Subscription Response Models ============


class SubscriptionResponse(BaseModel):
    tier: PlanTier
    status: SubscriptionStatus
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    limits: dict

    model_config = ConfigDict(from_attributes=True)


class UsageResponse(BaseModel):
    period_start: datetime
    credits_used: int
    credits_limit: int
    bonus_credits: int = 0

    model_config = ConfigDict(from_attributes=True)


class BillingOverview(BaseModel):
    subscription: SubscriptionResponse
    usage: UsageResponse
    credit_costs: dict
    usage_percentage: int
