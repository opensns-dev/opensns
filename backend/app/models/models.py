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

    default_llm_engine: str = "openai"
    default_image_engine: str = "fal"
    default_video_engine: str = "fal-video"
    default_ugc_engine: Optional[str] = None

    ugc_enabled: bool = False
    ugc_avatar_id: Optional[str] = None
    ugc_voice_id: Optional[str] = None

    ollama_url: Optional[str] = None
    comfyui_url: Optional[str] = None

    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="settings")


class UserSettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None
    heygen_api_key: Optional[str] = None
    did_api_key: Optional[str] = None
    default_llm_engine: Optional[str] = None
    default_image_engine: Optional[str] = None
    default_video_engine: Optional[str] = None
    default_ugc_engine: Optional[str] = None
    ugc_enabled: Optional[bool] = None
    ugc_avatar_id: Optional[str] = None
    ugc_voice_id: Optional[str] = None
    ollama_url: Optional[str] = None
    comfyui_url: Optional[str] = None


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
    has_openai_key: bool
    has_fal_key: bool
    has_firecrawl_key: bool
    has_heygen_key: bool
    has_did_key: bool

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
    "repurpose": 5,
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

    # Paddle integration
    paddle_customer_id: Optional[str] = Field(default=None, index=True)
    paddle_subscription_id: Optional[str] = Field(default=None, index=True)
    paddle_price_id: Optional[str] = None

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


class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(index=True, unique=True)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)

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
