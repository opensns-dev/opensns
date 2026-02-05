from typing import TypedDict, List, Optional, Literal, Annotated
import operator
from pydantic import BaseModel


class MarketingAngle(BaseModel):
    angle_title: str
    description: str
    target_persona: str


class AdCopy(BaseModel):
    headline: str
    body: str
    cta: str
    platform: str


class GeneratedAsset(BaseModel):
    asset_type: Literal["copy", "image", "video"]
    content: str
    platform: str
    metadata: dict = {}


class VerificationResult(BaseModel):
    passed: bool
    issues: List[str] = []
    suggestions: List[str] = []
    confidence: float = 0.0
    failed_items: List[str] = []


class CompetitorInsight(BaseModel):
    competitor_name: str
    strengths: List[str]
    weaknesses: List[str]
    ad_patterns: List[str]
    differentiation_opportunity: str


class PerformancePrediction(BaseModel):
    asset_id: str
    platform: str
    predicted_ctr: float
    predicted_engagement_rate: float
    confidence: float
    recommendations: List[str]


class AgentState(TypedDict):
    campaign_id: int
    user_id: int
    product_url: str
    product_context: str

    openai_api_key: Optional[str]
    fal_api_key: Optional[str]
    firecrawl_api_key: Optional[str]
    ollama_url: Optional[str]
    comfyui_url: Optional[str]
    heygen_api_key: Optional[str]
    did_api_key: Optional[str]
    default_llm_engine: Optional[str]
    default_image_engine: Optional[str]
    default_video_engine: Optional[str]
    default_ugc_engine: Optional[str]

    ugc_enabled: bool
    ugc_avatar_id: Optional[str]
    ugc_voice_id: Optional[str]

    research_data: Optional[dict]

    competitor_insights: Annotated[List[CompetitorInsight], operator.add]

    angles: Annotated[List[MarketingAngle], operator.add]
    generated_copies: Annotated[List[AdCopy], operator.add]
    generated_images: Annotated[List[GeneratedAsset], operator.add]
    generated_videos: Annotated[List[GeneratedAsset], operator.add]
    generated_ugc_videos: Annotated[List[GeneratedAsset], operator.add]
    optimized_assets: Annotated[List[GeneratedAsset], operator.add]

    performance_predictions: Annotated[List[PerformancePrediction], operator.add]

    verification_results: Annotated[List[VerificationResult], operator.add]
    verification_feedback: Optional[str]
    failed_items: Annotated[List[str], operator.add]

    current_step: str
    retry_count: int
    max_retries: int
    error: Optional[str]
    is_complete: bool

    copy_done: bool
    visual_done: bool
    ugc_done: bool

    requires_approval: bool
    is_approved: bool
