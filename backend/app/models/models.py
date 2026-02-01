from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from pydantic import BaseModel, EmailStr


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
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    campaigns: List["Campaign"] = Relationship(back_populates="user")
    settings: Optional["UserSettings"] = Relationship(back_populates="user")


class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


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

    updated_at: datetime = Field(default_factory=datetime.utcnow)

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

    class Config:
        from_attributes = True


# ============ Campaign Models ============


class CampaignBase(SQLModel):
    title: str
    product_url: str
    description: Optional[str] = None


class Campaign(CampaignBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    status: CampaignStatus = Field(default=CampaignStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    campaign: Campaign = Relationship(back_populates="assets")


class AgentLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    agent_name: str
    message: str
    level: str = "INFO"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    campaign: Campaign = Relationship(back_populates="agents")
