from datetime import datetime, UTC
from enum import Enum
import json
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import UniqueConstraint
from pydantic import BaseModel, ConfigDict, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


# ============ Subscription/Plan Enums ============


class PlanTier(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    BYOK = "BYOK"
    PRO = "PRO"
    ULTRA = "ULTRA"


class BillingPeriod(str, Enum):
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


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
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)

    campaigns: List["Campaign"] = Relationship(back_populates="user")
    settings: Optional["UserSettings"] = Relationship(back_populates="user")
    subscription: Optional["Subscription"] = Relationship(back_populates="user")
    usage: Optional["UsageTracking"] = Relationship(back_populates="user")
    repurpose_jobs: List["RepurposeJob"] = Relationship(back_populates="user")


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
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ============ User Settings Models ============


class UserSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    openai_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None
    heygen_api_key: Optional[str] = None
    did_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    sadtalker_url: Optional[str] = None

    default_llm_engine: str = "openai"
    default_image_engine: str = "fal"
    default_video_engine: str = "fal-video"
    default_ugc_engine: Optional[str] = None

    ugc_enabled: bool = False
    ugc_avatar_id: Optional[str] = None
    ugc_voice_id: Optional[str] = None

    ollama_url: Optional[str] = None
    comfyui_url: Optional[str] = None

    # Audio settings
    default_tts_engine: str = "openai-tts"
    default_bgm_engine: str = "static-bgm"
    default_stt_engine: str = "openai-stt"
    tts_enabled: bool = False
    bgm_enabled: bool = False
    tts_voice_id: Optional[str] = None
    bgm_style: Optional[str] = None

    ai_disclosure_enabled: bool = Field(default=True)
    ai_label_text: str = Field(default="AI Generated")
    ai_label_position: str = Field(
        default="BOTTOM_RIGHT"
    )  # TOP_LEFT|TOP_RIGHT|BOTTOM_LEFT|BOTTOM_RIGHT|NONE

    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="settings")


class UserSettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None
    heygen_api_key: Optional[str] = None
    did_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    sadtalker_url: Optional[str] = None
    default_llm_engine: Optional[str] = None
    default_image_engine: Optional[str] = None
    default_video_engine: Optional[str] = None
    default_ugc_engine: Optional[str] = None
    ugc_enabled: Optional[bool] = None
    ugc_avatar_id: Optional[str] = None
    ugc_voice_id: Optional[str] = None
    ollama_url: Optional[str] = None
    comfyui_url: Optional[str] = None
    default_tts_engine: Optional[str] = None
    default_bgm_engine: Optional[str] = None
    default_stt_engine: Optional[str] = None
    tts_enabled: Optional[bool] = None
    bgm_enabled: Optional[bool] = None
    tts_voice_id: Optional[str] = None
    bgm_style: Optional[str] = None
    ai_disclosure_enabled: Optional[bool] = None
    ai_label_text: Optional[str] = None
    ai_label_position: Optional[str] = None


class UserSettingsResponse(BaseModel):
    default_llm_engine: str
    default_image_engine: str
    default_video_engine: str
    default_ugc_engine: Optional[str]
    ugc_enabled: bool
    ugc_avatar_id: Optional[str]
    ugc_voice_id: Optional[str]
    ollama_url: Optional[str]
    comfyui_url: Optional[str]
    sadtalker_url: Optional[str]
    default_tts_engine: str
    default_bgm_engine: str
    default_stt_engine: str
    tts_enabled: bool
    bgm_enabled: bool
    tts_voice_id: Optional[str]
    bgm_style: Optional[str]
    has_openai_key: bool
    has_fal_key: bool
    has_firecrawl_key: bool
    has_heygen_key: bool
    has_did_key: bool
    has_anthropic_key: bool
    has_google_key: bool
    has_groq_key: bool
    ai_disclosure_enabled: bool
    ai_label_text: str
    ai_label_position: str

    model_config = ConfigDict(from_attributes=True)


# ============ Campaign Models ============


class CampaignBase(SQLModel):
    title: str
    product_url: str
    description: Optional[str] = None
    brand_kit_id: Optional[int] = Field(default=None, foreign_key="brandkit.id")
    template_id: Optional[int] = Field(default=None, foreign_key="template.id")


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
    AUDIO = "AUDIO"


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    type: AssetType
    content: str
    asset_metadata: str = Field(
        default="{}"
    )  # JSON string (renamed from 'metadata' which is reserved)
    ai_disclosure: str = Field(default="{}")  # JSON: {labeled, label_text, position}
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
    "repurpose": 5,
    "product_photo": 3,
    "tts": 2,
    "bgm": 0,
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
        "credits_per_month": 50,
        "team_members": 1,
        "api_access": False,
        "white_label": False,
        "competitor_research": False,
        "priority_queue": False,
        "credit_rollover": False,
        "byok": False,
        "annual_discount_percent": 0,
    },
    PlanTier.BASIC: {
        "price_monthly": 900,  # $9.00 in cents
        "credits_per_month": 150,
        "team_members": 1,
        "api_access": False,
        "white_label": False,
        "competitor_research": True,
        "priority_queue": False,
        "credit_rollover": False,
        "byok": False,
        "annual_discount_percent": 20,
    },
    PlanTier.BYOK: {
        "price_monthly": 1500,  # $15.00 in cents
        "credits_per_month": -1,  # unlimited (user's own keys)
        "team_members": 1,
        "api_access": False,
        "white_label": False,
        "competitor_research": True,
        "priority_queue": False,
        "credit_rollover": False,
        "byok": True,
        "annual_discount_percent": 20,
    },
    PlanTier.PRO: {
        "price_monthly": 2900,  # $29.00 in cents
        "credits_per_month": 500,
        "team_members": 3,
        "api_access": True,
        "white_label": False,
        "competitor_research": True,
        "priority_queue": True,
        "credit_rollover": True,
        "byok": False,
        "annual_discount_percent": 20,
    },
    PlanTier.ULTRA: {
        "price_monthly": 5900,  # $59.00 in cents
        "credits_per_month": 1200,
        "team_members": 10,
        "api_access": True,
        "white_label": True,
        "competitor_research": True,
        "priority_queue": True,
        "credit_rollover": True,
        "byok": False,
        "annual_discount_percent": 20,
    },
}

# Autopilot schedule limits per plan tier
AUTOPILOT_SCHEDULE_LIMITS = {
    PlanTier.FREE: 0,
    PlanTier.BASIC: 1,
    PlanTier.BYOK: 3,
    PlanTier.PRO: 3,
    PlanTier.ULTRA: 999,  # effectively unlimited
}


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    tier: PlanTier = Field(default=PlanTier.FREE)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE)

    # LemonSqueezy integration
    ls_customer_id: Optional[str] = Field(default=None, index=True)
    ls_subscription_id: Optional[str] = Field(default=None, index=True)
    ls_variant_id: Optional[str] = None

    # Billing cycle
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = Field(default=False)
    billing_period: BillingPeriod = Field(default=BillingPeriod.MONTHLY)

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
    rolled_over_credits: int = Field(default=0)
    bonus_credits: int = Field(default=0)

    total_credits_used: int = Field(default=0)
    total_images: int = Field(default=0)
    total_videos: int = Field(default=0)

    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional["User"] = Relationship(back_populates="usage")

    def reset_period(
        self, new_period_start: Optional[datetime] = None, rollover_credits: int = 0
    ):
        self.period_start = new_period_start or utc_now()
        self.rolled_over_credits = rollover_credits
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


class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(index=True, unique=True)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)

    user: Optional["User"] = Relationship()


# ============ Template / Concept Library Models ============


class TemplateIndustry(str, Enum):
    BEAUTY = "BEAUTY"
    HEALTH = "HEALTH"
    FOOD = "FOOD"
    IT_SAAS = "IT_SAAS"
    FASHION = "FASHION"
    EDUCATION = "EDUCATION"
    REAL_ESTATE = "REAL_ESTATE"
    FINANCE = "FINANCE"
    TRAVEL = "TRAVEL"
    PET = "PET"


class TemplatePlatform(str, Enum):
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    GOOGLE_ADS = "GOOGLE_ADS"
    NAVER = "NAVER"
    TIKTOK = "TIKTOK"


class TemplateLayout(str, Enum):
    SINGLE_IMAGE = "SINGLE_IMAGE"
    CAROUSEL = "CAROUSEL"
    VIDEO_COVER = "VIDEO_COVER"
    TEXT_OVERLAY = "TEXT_OVERLAY"
    SPLIT_VIEW = "SPLIT_VIEW"
    PRODUCT_HERO = "PRODUCT_HERO"


class Template(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    industry: TemplateIndustry
    platform: TemplatePlatform
    layout: TemplateLayout = Field(default=TemplateLayout.SINGLE_IMAGE)
    copy_template: str = ""  # JSON: {"headline": "...", "body": "...", "cta": "..."}
    style_config: str = "{}"  # JSON: colors, fonts, positioning hints
    preview_url: Optional[str] = None
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    industry: TemplateIndustry
    platform: TemplatePlatform
    layout: TemplateLayout
    copy_template: dict
    style_config: dict
    preview_url: Optional[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============ Brand Kit Models ============


class BrandKit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    is_default: bool = Field(default=False)

    # Visual identity
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None  # hex e.g. "#FF5733"
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_heading: Optional[str] = None
    font_body: Optional[str] = None

    # Brand voice
    tone_of_voice: Optional[str] = None  # e.g. "Professional yet friendly"
    brand_values: str = "[]"  # JSON array of strings
    target_audience: Optional[str] = None
    guidelines: Optional[str] = None  # Free-text brand guidelines

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class BrandKitCreate(BaseModel):
    name: str
    is_default: bool = False
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    tone_of_voice: Optional[str] = None
    brand_values: List[str] = []
    target_audience: Optional[str] = None
    guidelines: Optional[str] = None


class BrandKitUpdate(BaseModel):
    name: Optional[str] = None
    is_default: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    tone_of_voice: Optional[str] = None
    brand_values: Optional[List[str]] = None
    target_audience: Optional[str] = None
    guidelines: Optional[str] = None


class BrandKitResponse(BaseModel):
    id: int
    user_id: int
    name: str
    is_default: bool
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    font_heading: Optional[str]
    font_body: Optional[str]
    tone_of_voice: Optional[str]
    brand_values: List[str]
    target_audience: Optional[str]
    guidelines: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Publishing Models ============


class PublishPlatformType(str, Enum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    X = "X"
    THREADS = "THREADS"


class PublishStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class PublishConnection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    platform: PublishPlatformType
    access_token: str  # Encrypted via core/encryption.py
    refresh_token: Optional[str] = None  # Encrypted
    token_expires_at: Optional[datetime] = None
    account_id: Optional[str] = None  # e.g. Facebook Ad Account ID
    account_name: Optional[str] = None
    page_id: Optional[str] = None  # Facebook Page ID
    page_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class PublishLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    platform: PublishPlatformType
    status: PublishStatus = Field(default=PublishStatus.PENDING)
    external_post_id: Optional[str] = None  # Platform's post/ad ID
    external_url: Optional[str] = None  # Link to published post
    error_message: Optional[str] = None
    asset_ids: str = "[]"  # JSON array of asset IDs published
    publish_metadata: str = "{}"  # JSON: targeting, budget, etc.
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    campaign: Optional[Campaign] = Relationship()
    user: Optional[User] = Relationship()


class PublishRequest(BaseModel):
    platform: PublishPlatformType
    asset_ids: List[int] = []
    caption: Optional[str] = None
    targeting: Optional[dict] = None
    budget: Optional[dict] = None


class PublishConnectionResponse(BaseModel):
    id: int
    platform: PublishPlatformType
    account_id: Optional[str]
    account_name: Optional[str]
    page_id: Optional[str]
    page_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishLogResponse(BaseModel):
    id: int
    campaign_id: int
    platform: PublishPlatformType
    status: PublishStatus
    external_post_id: Optional[str]
    external_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ A/B Testing & Ad Variants ============


class AdVariant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    name: str
    variant_label: str = "A"  # A, B, C, D, E
    copy_headline: Optional[str] = None
    copy_body: Optional[str] = None
    copy_cta: Optional[str] = None
    image_asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    platform: Optional[str] = None
    is_control: bool = Field(default=False)
    variant_metadata: str = "{}"  # JSON
    created_at: datetime = Field(default_factory=utc_now)

    campaign: Optional[Campaign] = Relationship()


class AdVariantResponse(BaseModel):
    id: int
    campaign_id: int
    name: str
    variant_label: str
    copy_headline: Optional[str]
    copy_body: Optional[str]
    copy_cta: Optional[str]
    image_asset_id: Optional[int]
    platform: Optional[str]
    is_control: bool
    variant_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdVariantCreate(BaseModel):
    name: str
    variant_label: str = "A"
    copy_headline: Optional[str] = None
    copy_body: Optional[str] = None
    copy_cta: Optional[str] = None
    image_asset_id: Optional[int] = None
    platform: Optional[str] = None
    is_control: bool = False


# ============ Team Collaboration (RBAC) ============


class TeamRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class InviteStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class TeamMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_owner_id: int = Field(foreign_key="user.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    email: str = Field(index=True)
    role: TeamRole = Field(default=TeamRole.VIEWER)
    invite_status: InviteStatus = Field(default=InviteStatus.PENDING)
    invite_token: Optional[str] = Field(default=None, index=True)
    invited_at: datetime = Field(default_factory=utc_now)
    accepted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


class TeamMemberCreate(BaseModel):
    email: str
    role: TeamRole = TeamRole.EDITOR


class TeamMemberUpdate(BaseModel):
    role: Optional[TeamRole] = None


class TeamMemberResponse(BaseModel):
    id: int
    team_owner_id: int
    user_id: Optional[int]
    email: str
    role: TeamRole
    invite_status: InviteStatus
    invited_at: datetime
    accepted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============ Ad Performance Analytics ============


class AdPerformanceSource(str, Enum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    GOOGLE_ADS = "GOOGLE_ADS"
    MANUAL = "MANUAL"


class AdPerformance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    source: AdPerformanceSource
    date: datetime = Field(index=True)

    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    spend_cents: int = Field(default=0)
    revenue_cents: int = Field(default=0)

    ctr: Optional[float] = None
    cpc_cents: Optional[int] = None
    cpa_cents: Optional[int] = None
    roas: Optional[float] = None

    external_campaign_id: Optional[str] = None
    performance_metadata: str = "{}"  # JSON
    created_at: datetime = Field(default_factory=utc_now)

    campaign: Optional[Campaign] = Relationship()
    user: Optional[User] = Relationship()


class AdPerformanceResponse(BaseModel):
    id: int
    campaign_id: int
    source: AdPerformanceSource
    date: datetime
    impressions: int
    clicks: int
    conversions: int
    spend_cents: int
    revenue_cents: int
    ctr: Optional[float]
    cpc_cents: Optional[int]
    cpa_cents: Optional[int]
    roas: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdPerformanceSummary(BaseModel):
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_spend_cents: int
    total_revenue_cents: int
    avg_ctr: Optional[float]
    avg_cpc_cents: Optional[int]
    avg_roas: Optional[float]
    days_tracked: int


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


# ============ Public API Key Management ============


class ApiKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    key_prefix: str = Field(index=True)  # first 8 chars for lookup
    key_hash: str  # SHA-256 hash of full key
    scopes: str = Field(default="read,write")  # comma-separated
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class ApiKeyCreate(BaseModel):
    name: str
    scopes: Optional[str] = "read,write"
    expires_in_days: Optional[int] = None  # None = no expiry


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreatedResponse(BaseModel):
    id: int
    name: str
    key: str  # full key, shown only once
    key_prefix: str
    scopes: str
    expires_at: Optional[datetime]
    created_at: datetime


# ============ Prediction vs Actual Comparison ============


class PredictionComparison(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    predicted_ctr: Optional[float] = None
    predicted_engagement_rate: Optional[float] = None
    predicted_conversion_rate: Optional[float] = None
    predicted_quality_score: Optional[float] = None

    actual_ctr: Optional[float] = None
    actual_engagement_rate: Optional[float] = None
    actual_conversion_rate: Optional[float] = None
    actual_impressions: Optional[int] = None
    actual_clicks: Optional[int] = None
    actual_conversions: Optional[int] = None

    accuracy_score: Optional[float] = None  # 0-100 overall accuracy
    ctr_deviation: Optional[float] = None  # predicted - actual
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    campaign: Optional[Campaign] = Relationship()
    user: Optional[User] = Relationship()


class PredictionComparisonResponse(BaseModel):
    id: int
    campaign_id: int
    predicted_ctr: Optional[float]
    predicted_engagement_rate: Optional[float]
    predicted_conversion_rate: Optional[float]
    predicted_quality_score: Optional[float]
    actual_ctr: Optional[float]
    actual_engagement_rate: Optional[float]
    actual_conversion_rate: Optional[float]
    actual_impressions: Optional[int]
    actual_clicks: Optional[int]
    actual_conversions: Optional[int]
    accuracy_score: Optional[float]
    ctr_deviation: Optional[float]
    last_synced_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionAccuracySummary(BaseModel):
    total_campaigns: int
    avg_accuracy_score: Optional[float]
    avg_ctr_deviation: Optional[float]
    best_accuracy_campaign_id: Optional[int]
    worst_accuracy_campaign_id: Optional[int]
    prediction_count: int


# ============ Scheduled Publishing ============


class ScheduleStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScheduleRecurrence(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ScheduledPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    platform: str  # e.g. FACEBOOK, INSTAGRAM
    publish_connection_id: Optional[int] = Field(
        default=None, foreign_key="publishconnection.id"
    )

    scheduled_at: datetime = Field(index=True)
    published_at: Optional[datetime] = None
    status: ScheduleStatus = Field(default=ScheduleStatus.PENDING)
    recurrence: ScheduleRecurrence = Field(default=ScheduleRecurrence.NONE)

    asset_ids: str = Field(default="[]")  # JSON array of asset IDs
    copy_text: Optional[str] = None
    schedule_metadata: str = Field(default="{}")  # JSON
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    campaign: Optional[Campaign] = Relationship()
    user: Optional[User] = Relationship()


class ScheduledPostCreate(BaseModel):
    campaign_id: int
    platform: str
    scheduled_at: datetime
    publish_connection_id: Optional[int] = None
    recurrence: ScheduleRecurrence = ScheduleRecurrence.NONE
    asset_ids: Optional[List[int]] = None
    copy_text: Optional[str] = None


class ScheduledPostUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    platform: Optional[str] = None
    recurrence: Optional[ScheduleRecurrence] = None
    asset_ids: Optional[List[int]] = None
    copy_text: Optional[str] = None
    status: Optional[ScheduleStatus] = None


class ScheduledPostResponse(BaseModel):
    id: int
    campaign_id: int
    platform: str
    publish_connection_id: Optional[int]
    scheduled_at: datetime
    published_at: Optional[datetime]
    status: ScheduleStatus
    recurrence: ScheduleRecurrence
    asset_ids: List[int]
    copy_text: Optional[str]
    error: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarView(BaseModel):
    month: int
    year: int
    posts: List[ScheduledPostResponse]
    total_scheduled: int
    total_published: int
    total_failed: int


# ============ Autopilot Models ============


class AutopilotCadence(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class AutopilotRunStatus(str, Enum):
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    SKIPPED = "SKIPPED"


class AutopilotRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Schedule settings
    enabled: bool = Field(default=True)
    timezone: str = Field(default="Asia/Seoul")
    cadence: AutopilotCadence
    days_of_week: Optional[str] = None  # JSON: [0,2,4] where 0=Monday
    time_of_day: str = Field(default="09:00")  # HH:MM

    # Execution tracking
    next_run_at: datetime = Field(index=True)
    last_run_at: Optional[datetime] = None
    run_count: int = Field(default=0)
    consecutive_failures: int = Field(default=0)
    last_failure_reason: Optional[str] = None
    locked_until: Optional[datetime] = None  # Lock TTL 30min for idempotency

    # Generation settings
    product_url: str
    brand_kit_id: Optional[int] = None
    platform_targets: str = Field(default='["instagram"]')  # JSON array
    asset_types: str = Field(default='["image"]')  # JSON array, v1: image only
    num_variations: int = Field(default=3)

    # v2: Auto-publish settings
    auto_publish: bool = Field(default=False)
    publish_connection_ids: Optional[str] = None  # JSON array of PublishConnection IDs

    # Workflow settings
    requires_approval: bool = Field(default=True)  # v1: always True
    approval_timeout_hours: int = Field(default=48)

    # Meta
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AutopilotRunLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key="autopilotrule.id", index=True)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaign.id")
    status: AutopilotRunStatus

    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    credits_estimated: int = Field(default=0)
    credits_used: int = Field(default=0)
    retry_count: int = Field(default=0)
    publish_status: Optional[str] = None  # "pending", "published", "failed", "skipped"

class NotificationType(str, Enum):
    AUTOPILOT_COMPLETE = "AUTOPILOT_COMPLETE"
    AUTOPILOT_FAILED = "AUTOPILOT_FAILED"
    AUTOPILOT_DISABLED = "AUTOPILOT_DISABLED"
    CREDITS_LOW = "CREDITS_LOW"
    APPROVAL_NEEDED = "APPROVAL_NEEDED"
    PUBLISH_COMPLETE = "PUBLISH_COMPLETE"
    PUBLISH_FAILED = "PUBLISH_FAILED"


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    type: NotificationType
    title: str
    message: str
    is_read: bool = Field(default=False, index=True)
    metadata_json: Optional[str] = None  # JSON for extra context (campaign_id, rule_id, etc.)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AutopilotRuleCreate(BaseModel):
    product_url: str
    platform_targets: List[str] = ["instagram"]
    cadence: AutopilotCadence
    days_of_week: Optional[List[int]] = None
    time_of_day: str = "09:00"
    timezone: str = "Asia/Seoul"
    num_variations: int = 3
    brand_kit_id: Optional[int] = None
    asset_types: Optional[List[str]] = None
    requires_approval: Optional[bool] = None
    auto_publish: bool = False
    publish_connection_ids: Optional[List[int]] = None


class AutopilotRuleUpdate(BaseModel):
    platform_targets: Optional[List[str]] = None
    cadence: Optional[AutopilotCadence] = None
    days_of_week: Optional[List[int]] = None
    time_of_day: Optional[str] = None
    timezone: Optional[str] = None
    num_variations: Optional[int] = None
    brand_kit_id: Optional[int] = None
    product_url: Optional[str] = None
    asset_types: Optional[List[str]] = None
    auto_publish: Optional[bool] = None
    publish_connection_ids: Optional[List[int]] = None
    requires_approval: Optional[bool] = None


class AutopilotRuleResponse(BaseModel):
    id: int
    user_id: int
    enabled: bool
    timezone: str
    cadence: str
    days_of_week: Optional[List[int]]
    time_of_day: str
    next_run_at: datetime
    last_run_at: Optional[datetime]
    run_count: int
    consecutive_failures: int
    last_failure_reason: Optional[str]
    product_url: str
    brand_kit_id: Optional[int]
    platform_targets: List[str]
    asset_types: List[str]
    num_variations: int
    auto_publish: bool
    publish_connection_ids: Optional[List[int]]
    requires_approval: bool
    approval_timeout_hours: int
    created_at: datetime
    updated_at: datetime

    @field_validator("days_of_week", mode="before")
    @classmethod
    def parse_days_of_week(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("platform_targets", "asset_types", mode="before")
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("publish_connection_ids", mode="before")
    @classmethod
    def parse_connection_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = ConfigDict(from_attributes=True)


class AutopilotRunLogResponse(BaseModel):
    id: int
    rule_id: int
    campaign_id: Optional[int]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]
    credits_estimated: int
    credits_used: int
    retry_count: int
    publish_status: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    metadata_json: Optional[dict]
    created_at: datetime
    updated_at: datetime

    @field_validator("metadata_json", mode="before")
    @classmethod
    def parse_metadata(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (TypeError, json.JSONDecodeError):
                return None
        return v

    model_config = ConfigDict(from_attributes=True)


# ============ Custom Voice / Avatar ============


class VoiceCloneStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class CustomVoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    language: str = Field(default="en")
    sample_url: str  # URL to uploaded audio sample
    provider: str = Field(default="heygen")  # heygen, did, elevenlabs
    provider_voice_id: Optional[str] = None  # ID returned by provider after cloning
    status: VoiceCloneStatus = Field(default=VoiceCloneStatus.PENDING)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class CustomVoiceCreate(BaseModel):
    name: str
    language: str = "en"
    sample_url: str
    provider: str = "heygen"


class CustomVoiceResponse(BaseModel):
    id: int
    name: str
    language: str
    sample_url: str
    provider: str
    provider_voice_id: Optional[str]
    status: VoiceCloneStatus
    error: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomAvatar(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    provider: str = Field(default="heygen")  # heygen, did
    provider_avatar_id: Optional[str] = None
    preview_url: Optional[str] = None
    photo_url: str  # uploaded reference photo
    status: VoiceCloneStatus = Field(default=VoiceCloneStatus.PENDING)
    error: Optional[str] = None
    avatar_metadata: str = Field(default="{}")  # JSON
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class CustomAvatarCreate(BaseModel):
    name: str
    provider: str = "heygen"
    photo_url: str


class CustomAvatarResponse(BaseModel):
    id: int
    name: str
    provider: str
    provider_avatar_id: Optional[str]
    preview_url: Optional[str]
    photo_url: str
    status: VoiceCloneStatus
    error: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ White-Label Configuration ============


class WhiteLabelConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    brand_name: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = Field(default="#6366f1")  # hex color
    secondary_color: str = Field(default="#8b5cf6")  # hex color
    custom_domain: Optional[str] = None
    custom_css: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    hide_powered_by: bool = Field(default=False)
    is_active: bool = Field(default=False)
    config_metadata: str = Field(default="{}")  # JSON
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class WhiteLabelConfigCreate(BaseModel):
    brand_name: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"
    custom_domain: Optional[str] = None
    custom_css: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    hide_powered_by: bool = False


class WhiteLabelConfigUpdate(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    custom_css: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    hide_powered_by: Optional[bool] = None


class WhiteLabelConfigResponse(BaseModel):
    id: int
    brand_name: str
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: str
    secondary_color: str
    custom_domain: Optional[str]
    custom_css: Optional[str]
    email_from_name: Optional[str]
    email_from_address: Optional[str]
    hide_powered_by: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Ad Serving ============


class AdServingStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


class AdUnit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    name: str
    embed_code: Optional[str] = None  # auto-generated snippet
    target_url: str
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")

    status: AdServingStatus = Field(default=AdServingStatus.DRAFT)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    total_impressions: int = Field(default=0)
    total_clicks: int = Field(default=0)
    daily_impression_cap: Optional[int] = None
    daily_click_cap: Optional[int] = None

    serving_metadata: str = Field(default="{}")  # JSON: targeting, placement
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()
    campaign: Optional[Campaign] = Relationship()


class AdUnitCreate(BaseModel):
    campaign_id: int
    name: str
    target_url: str
    asset_id: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    daily_impression_cap: Optional[int] = None
    daily_click_cap: Optional[int] = None


class AdUnitUpdate(BaseModel):
    name: Optional[str] = None
    target_url: Optional[str] = None
    asset_id: Optional[int] = None
    status: Optional[AdServingStatus] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    daily_impression_cap: Optional[int] = None
    daily_click_cap: Optional[int] = None


class AdUnitResponse(BaseModel):
    id: int
    campaign_id: int
    name: str
    embed_code: Optional[str]
    target_url: str
    asset_id: Optional[int]
    status: AdServingStatus
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    total_impressions: int
    total_clicks: int
    daily_impression_cap: Optional[int]
    daily_click_cap: Optional[int]
    ctr: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdServingEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ad_unit_id: int = Field(foreign_key="adunit.id", index=True)
    event_type: str  # impression, click
    ip_hash: Optional[str] = None  # hashed IP for dedup
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class AdServingStats(BaseModel):
    ad_unit_id: int
    total_impressions: int
    total_clicks: int
    ctr: Optional[float]
    impressions_today: int
    clicks_today: int


# ============ Content Repurposing Models ============


class RepurposeStatus(str, Enum):
    PENDING = "PENDING"
    EXTRACTING = "EXTRACTING"
    TRANSCRIBING = "TRANSCRIBING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ToneStyle(str, Enum):
    FORMAL = "FORMAL"  # 존댓말/전문적
    CASUAL = "CASUAL"  # 반말/캐주얼
    FRIENDLY = "FRIENDLY"  # 존댓말/친근


class ContentPlatform(str, Enum):
    NAVER_BLOG = "NAVER_BLOG"
    X_THREAD = "X_THREAD"
    INSTAGRAM = "INSTAGRAM"
    BRUNCH = "BRUNCH"
    NAVER_POST = "NAVER_POST"
    SHORT_CLIP = "SHORT_CLIP"


class RepurposeJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    youtube_url: str
    video_title: Optional[str] = None
    video_duration: Optional[int] = None  # seconds
    status: RepurposeStatus = Field(default=RepurposeStatus.PENDING)
    tone_style: ToneStyle = Field(default=ToneStyle.FRIENDLY)
    target_platforms: str = Field(default="[]")  # JSON array of ContentPlatform values
    transcript: Optional[str] = None
    transcript_segments: Optional[str] = None  # JSON: [{start, end, text}]
    summary: Optional[str] = None
    key_points: Optional[str] = None  # JSON array of strings
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="repurpose_jobs")
    contents: List["RepurposeContent"] = Relationship(
        back_populates="job",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RepurposeContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="repurposejob.id")
    platform: ContentPlatform
    content: str
    content_metadata: str = Field(default="{}")  # JSON: hashtags, timestamps, etc.
    created_at: datetime = Field(default_factory=utc_now)

    job: Optional[RepurposeJob] = Relationship(back_populates="contents")


# ============ Repurpose Request/Response Schemas ============


class RepurposeJobCreate(BaseModel):
    youtube_url: str
    tone_style: ToneStyle = ToneStyle.FRIENDLY
    target_platforms: List[ContentPlatform] = [
        ContentPlatform.NAVER_BLOG,
        ContentPlatform.X_THREAD,
        ContentPlatform.INSTAGRAM,
        ContentPlatform.BRUNCH,
        ContentPlatform.NAVER_POST,
        ContentPlatform.SHORT_CLIP,
    ]


class RepurposeJobResponse(BaseModel):
    id: int
    youtube_url: str
    video_title: Optional[str]
    video_duration: Optional[int]
    status: RepurposeStatus
    tone_style: ToneStyle
    target_platforms: List[str]
    transcript: Optional[str]
    summary: Optional[str]
    key_points: Optional[List[str]]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepurposeContentResponse(BaseModel):
    id: int
    job_id: int
    platform: ContentPlatform
    content: str
    content_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Product Photography AI Models ============


class ProductPhotoStatus(str, Enum):
    PENDING = "PENDING"
    REMOVING_BG = "REMOVING_BG"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProductPhotoAngle(str, Enum):
    FRONT = "FRONT"
    SIDE = "SIDE"
    TOP_DOWN = "TOP_DOWN"
    LIFESTYLE = "LIFESTYLE"
    MODEL_HOLDING = "MODEL_HOLDING"
    STUDIO = "STUDIO"


class ProductPhoto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaign.id")
    original_image_url: str
    bg_removed_url: Optional[str] = None
    status: ProductPhotoStatus = Field(default=ProductPhotoStatus.PENDING)
    angles: str = Field(default="[]")  # JSON array of ProductPhotoAngle values
    results: str = Field(default="[]")  # JSON array of {angle, image_url}
    scene_prompt: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship()


class ProductPhotoCreate(BaseModel):
    original_image_url: str
    campaign_id: Optional[int] = None
    angles: List[ProductPhotoAngle] = [
        ProductPhotoAngle.FRONT,
        ProductPhotoAngle.LIFESTYLE,
        ProductPhotoAngle.STUDIO,
    ]
    scene_prompt: Optional[str] = None


# ============ Provider Credential Models ============


class ProviderCredential(SQLModel, table=True):
    """User credentials for AI providers.

    This table stores encrypted API keys and endpoint URLs for various AI providers.
    It supports the new provider-manager architecture while maintaining backward
    compatibility with the legacy UserSettings fields.
    """

    __table_args__ = (
        UniqueConstraint("user_id", "provider_name", name="uix_user_provider"),
        {"sqlite_autoincrement": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Provider identification
    provider_type: str = Field(index=True)  # llm, image, video, ugc, scraper
    provider_name: str = Field(index=True)  # openai, fal, heygen, etc.

    # Encrypted credentials
    credential_key: Optional[str] = None  # Encrypted API key
    endpoint_url: Optional[str] = (
        None  # For self-hosted providers (ollama, comfyui, etc.)
    )

    # Status
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationship
    user: Optional[User] = Relationship()


class ProviderCredentialUpsert(BaseModel):
    """Schema for creating or updating a provider credential."""

    provider_name: str
    credential_key: Optional[str] = None  # Raw API key (will be encrypted)
    endpoint_url: Optional[str] = None
    is_active: bool = True


class ProviderCredentialResponse(BaseModel):
    """Schema for returning a provider credential (without secrets)."""

    id: int
    user_id: int
    provider_type: str
    provider_name: str
    has_credential_key: bool  # True if a key is stored (but not returned)
    endpoint_url: Optional[str]  # URLs are safe to return
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderRegistryItemResponse(BaseModel):
    """Schema for provider registry items (static metadata)."""

    provider_type: str
    provider_name: str
    display_name: str
    description: str
    requires_key: bool
    requires_url: bool
    shared_key_provider: Optional[str] = None
    shared_url_provider: Optional[str] = None
    docs_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProviderCredentialTestResult(BaseModel):
    """Schema for provider credential test results."""

    provider_name: str
    success: bool
    message: str
    test_type: str = "connectivity"
    capabilities: Optional[dict] = None


# ============ Product Photography AI Models ============


class ProductPhotoResponse(BaseModel):
    id: int
    user_id: int
    campaign_id: Optional[int]
    original_image_url: str
    bg_removed_url: Optional[str]
    status: ProductPhotoStatus
    angles: List[str]
    results: List[dict]
    scene_prompt: Optional[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Waitlist Models ============


class WaitlistEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    source: str = Field(default="coming_soon")  # where they signed up from
    created_at: datetime = Field(default_factory=utc_now)


class WaitlistRequest(BaseModel):
    email: str


class WaitlistResponse(BaseModel):
    id: int
    email: str
    source: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
