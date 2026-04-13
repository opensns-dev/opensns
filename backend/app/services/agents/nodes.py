import json
import logging
import re
import tempfile
from typing import List, Any, Optional

import httpx

from app.services.agents.state import (
    AgentState,
    MarketingAngle,
    AdCopy,
    GeneratedAsset,
    VerificationResult,
    CompetitorInsight,
    PerformancePrediction,
)
from app.core.registry import engine_registry
from app.core.config import settings
from app.core.exceptions import APIKeyNotConfiguredError, EngineNotFoundError
from app.core.interfaces import AdCreative
from app.core.sanitization import sanitize_for_prompt, sanitize_url

logger = logging.getLogger(__name__)

PLATFORM_SPECS = {
    # Instagram
    "instagram_feed": {"width": 1080, "height": 1080, "aspect_ratio": "1:1"},
    "instagram_story": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
    # Facebook
    "facebook_feed": {"width": 1200, "height": 628, "aspect_ratio": "1.91:1"},
    # Google Ads
    "google_ads_landscape": {"width": 1200, "height": 628, "aspect_ratio": "1.91:1"},
    "google_ads_square": {"width": 1200, "height": 1200, "aspect_ratio": "1:1"},
    # TikTok
    "tiktok": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
    # Naver Search Ads
    "naver_search_power_link": {
        "width": None,
        "height": None,
        "aspect_ratio": None,
        "text_limits": {"title": 15, "description": 45},
        "description": "Search result text ads (파워링크)",
    },
    "naver_search_brand": {
        "width": 290,
        "height": 80,
        "aspect_ratio": "29:8",
        "text_limits": {"title": 25, "description": 100},
        "description": "Brand search premium placement (브랜드검색)",
    },
    # Naver GFA (Display Ads)
    "naver_gfa_native_feed": {
        "width": 1200,
        "height": 628,
        "aspect_ratio": "1.91:1",
        "text_limits": {"title": 25, "description": 45},
        "description": "Native feed ads in Naver services",
    },
    "naver_gfa_banner_large": {
        "width": 970,
        "height": 250,
        "aspect_ratio": "97:25",
        "description": "Large banner on Naver main page",
    },
    "naver_gfa_banner_medium": {
        "width": 300,
        "height": 250,
        "aspect_ratio": "6:5",
        "description": "Medium rectangle banner",
    },
    "naver_gfa_mobile_native": {
        "width": 1080,
        "height": 1080,
        "aspect_ratio": "1:1",
        "text_limits": {"title": 20, "description": 40},
        "description": "Mobile native ads in Naver app",
    },
    # Naver Shopping Ads
    "naver_shopping_product": {
        "width": 500,
        "height": 500,
        "aspect_ratio": "1:1",
        "text_limits": {"title": 50},
        "description": "Product image for Naver Shopping",
    },
    "naver_shopping_brand_zone": {
        "width": 1200,
        "height": 400,
        "aspect_ratio": "3:1",
        "description": "Brand zone banner in Naver Shopping",
    },
    # Naver Blog/Cafe (Content Marketing)
    "naver_blog_thumbnail": {
        "width": 966,
        "height": 520,
        "aspect_ratio": "1.86:1",
        "description": "Blog post featured image",
    },
    "naver_cafe_banner": {
        "width": 1024,
        "height": 180,
        "aspect_ratio": "5.69:1",
        "description": "Cafe community banner",
    },
    # Naver TV / Video
    "naver_tv_instream": {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "video_length": {"min": 6, "max": 60},
        "description": "In-stream video ads in Naver TV",
    },
    "naver_shorts": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "video_length": {"min": 5, "max": 60},
        "description": "Short-form video for Naver Clip",
    },
}


def _extract_json(text: str) -> dict[str, Any]:
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        text = json_match.group(1)

    text = text.strip()
    if not text.startswith("{") and not text.startswith("["):
        start = text.find("{")
        if start != -1:
            text = text[start:]

    return json.loads(text)


_temp_files: dict[int, list[str]] = {}


def _save_to_temp(data: bytes, suffix: str, prefix: str, campaign_id: int = 0) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False)
    tmp.write(data)
    tmp.close()
    _temp_files.setdefault(campaign_id, []).append(tmp.name)
    return tmp.name


def cleanup_temp_files(campaign_id: int = 0):
    import os

    paths = _temp_files.pop(campaign_id, [])
    for path in paths:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass


def _get_llm_engine(state: AgentState):
    engine_name = state.get("default_llm_engine") or settings.DEFAULT_LLM_ENGINE
    openai_key = state.get("openai_api_key")
    ollama_url = state.get("ollama_url")

    try:
        if engine_name == "openai" and openai_key:
            from app.services.openai_adapter import OpenAIAdapter

            return OpenAIAdapter(api_key=openai_key)
        elif engine_name == "ollama" and ollama_url:
            from app.services.ollama_adapter import OllamaAdapter

            return OllamaAdapter(base_url=ollama_url)
        else:
            return engine_registry.get_llm_engine(engine_name)
    except (EngineNotFoundError, APIKeyNotConfiguredError) as e:
        logger.warning(f"Failed to get {engine_name} engine: {e}. Using fallback LLM.")
        return engine_registry.get_llm_engine("fallback")


def _get_image_engine(state: AgentState):
    engine_name = state.get("default_image_engine") or settings.DEFAULT_IMAGE_ENGINE
    fal_key = state.get("fal_api_key")
    comfyui_url = state.get("comfyui_url")

    try:
        if engine_name == "fal" and fal_key:
            from app.services.image.fal_adapter import FalAIAdapter

            return FalAIAdapter(api_key=fal_key)
        elif engine_name == "comfyui" and comfyui_url:
            from app.services.image.comfyui_adapter import ComfyUIAdapter

            return ComfyUIAdapter(base_url=comfyui_url)
        else:
            return engine_registry.get_image_engine(engine_name)
    except (EngineNotFoundError, ValueError) as e:
        logger.warning(f"Failed to get {engine_name} engine: {e}. Using fallback.")
        return None


def _get_video_engine(state: AgentState):
    engine_name = state.get("default_video_engine") or settings.DEFAULT_VIDEO_ENGINE
    fal_key = state.get("fal_api_key")
    comfyui_url = state.get("comfyui_url")

    try:
        if engine_name == "fal-video" and fal_key:
            from app.services.video.fal_video_adapter import FalVideoAdapter

            return FalVideoAdapter(api_key=fal_key)
        elif engine_name == "comfyui-video" and comfyui_url:
            from app.services.video.comfyui_video_adapter import ComfyUIVideoAdapter

            return ComfyUIVideoAdapter(base_url=comfyui_url)
        else:
            return engine_registry.get_video_engine(engine_name)
    except (EngineNotFoundError, ValueError) as e:
        logger.warning(f"Failed to get {engine_name} engine: {e}. Using fallback.")
        return None


async def _fetch_product_image(state: AgentState) -> Optional[bytes]:
    research_data = state.get("research_data")
    if not research_data:
        return None

    images = research_data.get("images", [])
    if not images:
        return None

    image_url = images[0]
    if not image_url or not image_url.startswith(("http://", "https://")):
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                image_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "image" in content_type or image_url.endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".gif")
            ):
                # Verify image is large enough for ad generation (min 256x256)
                from PIL import Image
                import io

                try:
                    img = Image.open(io.BytesIO(response.content))
                    w, h = img.size
                    if w < 256 or h < 256:
                        logger.warning(
                            f"Product image too small ({w}x{h}), skipping for txt2img fallback"
                        )
                        return None
                except Exception:
                    pass

                logger.info(f"Fetched product image: {len(response.content)} bytes")
                return response.content
    except Exception as e:
        logger.warning(f"Failed to fetch product image from {image_url}: {e}")

    return None


def _get_fallback_image_url(state: AgentState, angle_title: str) -> str:
    research_data = state.get("research_data") or {}
    images = research_data.get("images", [])
    if images:
        return images[0]
    return f"https://placehold.co/1080x1080/f3f4f6/64748b?text={angle_title.replace(' ', '+')}"


def _get_default_image_bytes() -> bytes:
    """Generate a 512x512 default product image for ComfyUI compatibility."""
    from PIL import Image, ImageDraw
    import io

    img = Image.new("RGB", (512, 512), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    # Simple product placeholder shape
    draw.rectangle([156, 156, 356, 356], fill=(220, 220, 220), outline=(200, 200, 200))
    draw.rectangle([176, 176, 336, 336], fill=(235, 235, 235), outline=(210, 210, 210))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_fallback_angles(product_context: str) -> List[MarketingAngle]:
    return [
        MarketingAngle(
            angle_title="Convenience",
            description="Focus on ease of use and time-saving benefits",
            target_persona="Busy professionals aged 25-45",
        ),
        MarketingAngle(
            angle_title="Quality",
            description="Emphasize premium materials and craftsmanship",
            target_persona="Quality-conscious consumers",
        ),
        MarketingAngle(
            angle_title="Value",
            description="Highlight cost-effectiveness and ROI",
            target_persona="Budget-minded shoppers",
        ),
    ]


def _generate_fallback_competitor_insights() -> List[CompetitorInsight]:
    return [
        CompetitorInsight(
            competitor_name="Market Leader",
            strengths=["Established brand recognition", "Wide distribution network"],
            weaknesses=["Premium pricing", "Slower innovation cycle"],
            ad_patterns=["Trust-based messaging", "Lifestyle imagery"],
            differentiation_opportunity="Position as innovative alternative with better value",
        )
    ]


async def research_node(state: AgentState) -> dict[str, Any]:
    from app.services.research import ResearchService

    firecrawl_key = state.get("firecrawl_api_key")
    research_service = ResearchService(firecrawl_api_key=firecrawl_key)

    product_url = sanitize_url(state.get("product_url", ""))
    if not product_url:
        return {
            "product_context": "Invalid or missing product URL",
            "research_data": {},
            "current_step": "competitor_analysis",
        }

    research_data = await research_service.scrape_url(product_url)

    title = sanitize_for_prompt(research_data.get("title", "Unknown"), max_length=200)
    description = sanitize_for_prompt(
        research_data.get("description", "No description"), max_length=500
    )
    features = [
        sanitize_for_prompt(f, max_length=100)
        for f in research_data.get("features", [])
    ]
    content = sanitize_for_prompt(research_data.get("content", ""), max_length=1500)
    price = sanitize_for_prompt(
        str(research_data.get("price") or "Not available"), max_length=50
    )
    source = sanitize_for_prompt(research_data.get("source", "unknown"), max_length=100)

    features_str = ", ".join(features)
    images_str = ", ".join(research_data.get("images", [])[:3])

    product_context = f"""
    Title: {title}
    Description: {description}
    Features: {features_str or "Not available"}
    Price: {price}
    Images: {images_str or "Not available"}
    Content: {content}
    Source: {source}
    """

    return {
        "product_context": product_context,
        "research_data": research_data,
        "current_step": "competitor_analysis",
    }


async def competitor_analysis_node(state: AgentState) -> dict[str, Any]:
    llm = _get_llm_engine(state)

    prompt = f"""Analyze potential competitors for the following product and identify marketing opportunities.

Product Information:
{state.get("product_context", "No context available")}

Return a JSON object with competitor insights:
{{
    "competitors": [
        {{
            "competitor_name": "Name of competitor",
            "strengths": ["list of their strengths"],
            "weaknesses": ["list of their weaknesses"],
            "ad_patterns": ["common advertising patterns they use"],
            "differentiation_opportunity": "How our product can differentiate"
        }}
    ]
}}

Identify 2-3 main competitors and provide actionable insights."""

    try:
        response = await llm.generate_text(prompt)
        parsed = _extract_json(response)
        insights = [CompetitorInsight(**c) for c in parsed.get("competitors", [])]

        if not insights:
            insights = _generate_fallback_competitor_insights()
    except Exception as e:
        logger.warning(f"Competitor analysis failed: {e}. Using fallback.")
        insights = _generate_fallback_competitor_insights()

    return {
        "competitor_insights": insights,
        "current_step": "strategy",
    }


async def strategy_node(state: AgentState) -> dict[str, Any]:
    llm = _get_llm_engine(state)

    competitor_context = ""
    for insight in state.get("competitor_insights", []):
        competitor_context += f"""
Competitor: {insight.competitor_name}
- Differentiation opportunity: {insight.differentiation_opportunity}
"""

    prompt = f"""Analyze the following product information and generate 3 distinct marketing angles.
Each angle should highlight a different facet of the SAME core product value proposition.
The angles must be complementary — they should reinforce a unified brand message, not tell disconnected stories.

Product Information:
{state.get("product_context", "No context available")}

Competitor Analysis:
{competitor_context or "No competitor data available"}

Return a JSON object with the following structure:
{{
    "angles": [
        {{
            "angle_title": "Title of the marketing angle",
            "description": "Detailed description of the marketing approach",
            "target_persona": "Description of the target audience"
        }}
    ]
}}

IMPORTANT:
- All 3 angles must be about the SAME product and its primary value proposition.
- Each angle targets a different audience segment or emotional trigger, but they share a common product narrative.
- Do NOT create angles about unrelated product features. Instead, frame the same core benefit from 3 perspectives.
Generate exactly 3 angles."""

    try:
        response = await llm.generate_text(prompt)
        parsed = _extract_json(response)
        angles = [MarketingAngle(**a) for a in parsed.get("angles", [])]

        if not angles:
            angles = _generate_fallback_angles(state.get("product_context", ""))
    except Exception as e:
        logger.warning(f"Failed to generate angles via LLM: {e}. Using fallback.")
        angles = _generate_fallback_angles(state.get("product_context", ""))

    return {
        "angles": angles,
        "current_step": "parallel_generation",
    }


def route_after_strategy(state: AgentState) -> List[str]:
    if state.get("requires_approval") and not state.get("is_approved"):
        return ["approval"]
    return ["copy_generation", "image_generation"]


async def copy_generation_node(state: AgentState) -> dict[str, Any]:
    llm = _get_llm_engine(state)
    generated_copies: List[AdCopy] = []
    platforms = ["instagram", "facebook", "google_ads"]

    feedback_context = ""
    if state.get("verification_feedback"):
        feedback_context = f"""
IMPORTANT: Previous generation failed verification.
Feedback to address: {state.get("verification_feedback")}
Failed items: {", ".join(state.get("failed_items", []))}
Please fix these issues in the new generation.
"""

    brand_voice_context = ""
    brand_kit = state.get("brand_kit")
    if brand_kit:
        parts = []
        if brand_kit.get("tone_of_voice"):
            parts.append(f"Tone of Voice: {brand_kit['tone_of_voice']}")
        if brand_kit.get("brand_values"):
            values = brand_kit["brand_values"]
            if isinstance(values, list):
                values = ", ".join(values)
            parts.append(f"Brand Values: {values}")
        if brand_kit.get("target_audience"):
            parts.append(f"Target Audience: {brand_kit['target_audience']}")
        if brand_kit.get("guidelines"):
            parts.append(f"Brand Guidelines: {brand_kit['guidelines']}")
        if parts:
            brand_voice_context = (
                "\n\nBrand Voice:\n"
                + "\n".join(parts)
                + "\nEnsure all copy aligns with the brand voice above.\n"
            )

    angles = state.get("angles", [])

    angles_section = ""
    for i, angle in enumerate(angles, 1):
        angles_section += f"""
Angle {i}: {angle.angle_title}
- Description: {angle.description}
- Target Audience: {angle.target_persona}
"""

    total_copies = len(angles) * len(platforms)

    prompt = f"""Generate ad copy for a unified marketing campaign.

Product Context:
{state.get("product_context", "No context available")}
{feedback_context}
{brand_voice_context}

MARKETING ANGLES:
{angles_section}

TARGET PLATFORMS: {", ".join(platforms)}

CAMPAIGN CONSISTENCY RULES:
- ALL copies must share a CONSISTENT brand voice, tone, and messaging style.
- They should feel like parts of ONE cohesive campaign, not separate campaigns.
- Each angle can emphasize different product features, but the overall tone, language style, and energy level must remain uniform.
- Use a consistent CTA style across all copies.

IMPORTANT RULES:
- Focus on THIS product's strengths and unique value proposition.
- Do NOT mention competitor names or make direct comparisons to other brands.
- Do NOT use phrases like "unlike X" or "better than Y".
- Highlight what makes the product great on its own merits.
- PRICING: Only include specific prices if they appear EXACTLY in the Product Context above. If you are unsure about exact pricing, do NOT mention any price, dollar amount, or "starting from" claim. Getting a price wrong is a critical error.

Generate exactly {total_copies} copies: one for each combination of angle and platform.

Return a JSON object with the following structure:
{{
    "copies": [
        {{
            "headline": "Compelling headline for the ad",
            "body": "Ad body text (appropriate length for the platform)",
            "cta": "Call to action text",
            "platform": "platform_name"
        }}
    ]
}}

Order: Angle 1 × all platforms, then Angle 2 × all platforms, etc.
Generate exactly {total_copies} copies total."""

    try:
        response = await llm.generate_text(prompt)
        parsed = _extract_json(response)
        copies = [AdCopy(**c) for c in parsed.get("copies", [])]
        generated_copies.extend(copies)
    except Exception as e:
        logger.warning(
            f"Failed to generate copies in single call: {e}. Using template fallback."
        )
        for angle in angles:
            for platform in platforms:
                copy = AdCopy(
                    headline=f"{angle.angle_title}: Discover the Difference",
                    body=f"Experience {angle.description.lower()}. Perfect for {angle.target_persona.lower()}.",
                    cta="Shop Now",
                    platform=platform,
                )
                generated_copies.append(copy)

    return {
        "generated_copies": generated_copies,
        "copy_done": True,
        "current_step": "merge_branches",
    }


async def image_generation_node(state: AgentState) -> dict[str, Any]:
    image_engine = _get_image_engine(state)
    generated_images: List[GeneratedAsset] = []

    product_image = await _fetch_product_image(state)
    has_product_image = product_image is not None

    feedback_context = ""
    verification_feedback = state.get("verification_feedback") or ""
    if verification_feedback and "image" in verification_feedback.lower():
        feedback_context = f"Address this feedback: {verification_feedback}"

    research_data = state.get("research_data") or {}
    product_title = research_data.get("title", "Product")
    product_features = ", ".join(research_data.get("features", [])[:3])

    brand_visual_context = ""
    brand_kit = state.get("brand_kit")
    if brand_kit:
        visual_parts = []
        if brand_kit.get("primary_color"):
            visual_parts.append(f"primary color {brand_kit['primary_color']}")
        if brand_kit.get("secondary_color"):
            visual_parts.append(f"secondary color {brand_kit['secondary_color']}")
        if brand_kit.get("accent_color"):
            visual_parts.append(f"accent color {brand_kit['accent_color']}")
        if brand_kit.get("font_heading"):
            visual_parts.append(f"heading font {brand_kit['font_heading']}")
        if brand_kit.get("font_body"):
            visual_parts.append(f"body font {brand_kit['font_body']}")
        if visual_parts:
            brand_visual_context = f", brand palette: {', '.join(visual_parts)}"

    for angle in state.get("angles", []):
        if image_engine is None:
            fallback_image_url = _get_fallback_image_url(state, angle.angle_title)
            asset = GeneratedAsset(
                asset_type="image",
                content=fallback_image_url,
                platform="instagram",
                metadata={
                    "angle": angle.angle_title,
                    "fallback": True,
                    "reason": "No image engine configured",
                },
            )
            generated_images.append(asset)
            continue

        try:
            prompt_suffix = f" {feedback_context}" if feedback_context else ""
            image_prompt = (
                f"Professional product advertisement for {product_title}, "
                f"marketing angle: {angle.angle_title}, "
                f"features: {product_features or 'premium quality'}, "
                f"clean modern background, studio lighting, commercial quality"
                f"{brand_visual_context}{prompt_suffix}"
            )

            creative = AdCreative(
                title=angle.angle_title,
                body=angle.description,
                platform="instagram",
                image_prompt=image_prompt,
            )

            if has_product_image:
                result = await image_engine.generate_ad_image(product_image, creative)
            else:
                from app.services.image.comfyui_adapter import ComfyUIAdapter

                if isinstance(image_engine, ComfyUIAdapter):
                    result = await image_engine.generate_text_to_image(creative)
                else:
                    source_image = _get_default_image_bytes()
                    result = await image_engine.generate_ad_image(
                        source_image, creative
                    )

            asset = GeneratedAsset(
                asset_type="image",
                content=result.image_url or "generated_image_data",
                platform="instagram",
                metadata={
                    "angle": angle.angle_title,
                    "prompt": creative.image_prompt,
                    "used_product_image": has_product_image,
                    **result.metadata,
                },
            )
            generated_images.append(asset)
        except Exception as e:
            logger.warning(
                f"Image generation failed for {angle.angle_title}: {e}. Using fallback."
            )
            fallback_image_url = _get_fallback_image_url(state, angle.angle_title)
            asset = GeneratedAsset(
                asset_type="image",
                content=fallback_image_url,
                platform="instagram",
                metadata={
                    "angle": angle.angle_title,
                    "fallback": True,
                    "error": str(e),
                },
            )
            generated_images.append(asset)

    return {
        "generated_images": generated_images,
        "current_step": "video_generation",
    }


async def video_generation_node(state: AgentState) -> dict[str, Any]:
    video_engine = _get_video_engine(state)
    generated_videos: List[GeneratedAsset] = []

    images = state.get("generated_images", [])
    for image in images[:1]:
        angle_name = image.metadata.get("angle", "default")
        is_fallback_image = image.metadata.get("fallback", False)

        if video_engine is None:
            video_asset = GeneratedAsset(
                asset_type="video",
                content=image.content,
                platform="tiktok",
                metadata={
                    "source_image": image.content,
                    "fallback": True,
                    "reason": "No video engine configured",
                },
            )
            generated_videos.append(video_asset)
            continue

        try:
            image_prompt = image.metadata.get("prompt", "")
            if image_prompt:
                motion_prompt = f"{image_prompt}, smooth camera motion, cinematic"
            else:
                motion_prompt = (
                    "Smooth camera pan, product showcase, professional advertisement"
                )

            result = await video_engine.image_to_video(
                image_url=image.content,
                motion_prompt=motion_prompt,
                duration=5.0,
            )

            video_asset = GeneratedAsset(
                asset_type="video",
                content=result.video_url or "generated_video_data",
                platform="tiktok",
                metadata={
                    "source_image": image.content,
                    "image_prompt": image_prompt,
                    "duration": result.duration,
                    "used_fallback_image": is_fallback_image,
                    **result.metadata,
                },
            )
            generated_videos.append(video_asset)
        except Exception as e:
            logger.warning(
                f"Video generation failed for {angle_name}: {e}. Using source image as fallback."
            )
            video_asset = GeneratedAsset(
                asset_type="video",
                content=image.content,
                platform="tiktok",
                metadata={
                    "source_image": image.content,
                    "fallback": True,
                    "error": str(e),
                },
            )
            generated_videos.append(video_asset)

    return {
        "generated_videos": generated_videos,
        "visual_done": True,
        "current_step": "merge_branches",
    }


def _get_ugc_engine(state: AgentState):
    engine_name = state.get("default_ugc_engine") or "heygen"
    heygen_key = state.get("heygen_api_key")
    did_key = state.get("did_api_key")

    try:
        if engine_name == "heygen" and heygen_key:
            from app.services.video.heygen_adapter import HeyGenAdapter

            return HeyGenAdapter(api_key=heygen_key)
        elif engine_name == "d-id" and did_key:
            from app.services.video.did_adapter import DIDAdapter

            return DIDAdapter(api_key=did_key)
        else:
            engine = engine_registry.get_video_engine(engine_name)
            if engine and engine.supports_ugc():
                return engine
            return engine_registry.get_video_engine("heygen")
    except (EngineNotFoundError, ValueError) as e:
        logger.warning(f"Failed to get {engine_name} UGC engine: {e}.")
        return None


def _get_tts_engine(state: AgentState):
    """Get TTS engine from user config or registry."""
    engine_name = state.get("default_tts_engine") or "openai-tts"
    openai_key = state.get("openai_api_key")

    try:
        if engine_name == "openai-tts" and openai_key:
            from app.services.audio.tts import OpenAITTSAdapter

            return OpenAITTSAdapter(api_key=openai_key)
        else:
            return engine_registry.get_tts_engine(engine_name)
    except (EngineNotFoundError, ValueError) as e:
        logger.warning(
            f"Failed to get {engine_name} TTS engine: {e}. Trying edge-tts fallback."
        )
        return engine_registry.get_tts_engine_or_none("edge-tts")


def _get_bgm_engine(state: AgentState):
    """Get BGM engine from user config or registry."""
    engine_name = state.get("default_bgm_engine") or "static-bgm"
    try:
        return engine_registry.get_bgm_engine(engine_name)
    except (EngineNotFoundError, ValueError) as e:
        logger.warning(
            f"Failed to get {engine_name} BGM engine: {e}. Trying static-bgm fallback."
        )
        return engine_registry.get_bgm_engine_or_none("static-bgm")


async def ugc_video_generation_node(state: AgentState) -> dict[str, Any]:
    if not state.get("ugc_enabled", False):
        return {
            "generated_ugc_videos": [],
            "ugc_done": True,
            "current_step": "merge_branches",
        }

    ugc_engine = _get_ugc_engine(state)
    generated_ugc_videos: List[GeneratedAsset] = []

    copies = state.get("generated_copies", [])
    if not copies:
        logger.warning("No ad copies available for UGC video generation")
        return {
            "generated_ugc_videos": [],
            "ugc_done": True,
            "current_step": "merge_branches",
        }

    copy = copies[0]
    script = f"{copy.headline}. {copy.body}. {copy.cta}"

    if ugc_engine is None:
        ugc_asset = GeneratedAsset(
            asset_type="video",
            content="",
            platform="tiktok",
            metadata={
                "type": "ugc",
                "fallback": True,
                "reason": "No UGC engine configured",
                "script": script[:100],
            },
        )
        generated_ugc_videos.append(ugc_asset)
        return {
            "generated_ugc_videos": generated_ugc_videos,
            "ugc_done": True,
            "current_step": "merge_branches",
        }

    try:
        from app.services.video.interfaces import UGCVideoRequest

        request = UGCVideoRequest(
            script=script,
            avatar_id=state.get("ugc_avatar_id"),
            voice_id=state.get("ugc_voice_id"),
            language="en",
            aspect_ratio="9:16",
        )

        result = await ugc_engine.generate_ugc_video(request)

        ugc_asset = GeneratedAsset(
            asset_type="video",
            content=result.video_url or "",
            platform="tiktok",
            metadata={
                "type": "ugc",
                "script": script[:100],
                "duration": result.duration,
                "avatar_id": state.get("ugc_avatar_id"),
                "voice_id": state.get("ugc_voice_id"),
                **result.metadata,
            },
        )
        generated_ugc_videos.append(ugc_asset)

    except Exception as e:
        logger.warning(f"UGC video generation failed: {e}. Using fallback.")
        ugc_asset = GeneratedAsset(
            asset_type="video",
            content="",
            platform="tiktok",
            metadata={
                "type": "ugc",
                "fallback": True,
                "error": str(e),
                "script": script[:100],
            },
        )
        generated_ugc_videos.append(ugc_asset)

    return {
        "generated_ugc_videos": generated_ugc_videos,
        "ugc_done": True,
        "current_step": "merge_branches",
    }


async def tts_generation_node(state: AgentState) -> dict[str, Any]:
    """Generate TTS narration from ad copy."""
    if not state.get("tts_enabled", False):
        return {
            "generated_tts": [],
            "tts_done": True,
            "current_step": "audio_mixing",
        }

    tts_engine = _get_tts_engine(state)
    generated_tts = []

    copies = state.get("generated_copies", [])
    if not copies:
        logger.warning("No ad copies available for TTS generation")
        return {
            "generated_tts": [],
            "tts_done": True,
            "current_step": "audio_mixing",
        }

    # Primary ad copy → narration script
    copy = copies[0]
    script = f"{copy.headline}. {copy.body}. {copy.cta}"

    if tts_engine is None:
        logger.warning("No TTS engine available")
        return {
            "generated_tts": [],
            "tts_done": True,
            "current_step": "audio_mixing",
        }

    try:
        from app.services.audio.interfaces import TTSRequest

        request = TTSRequest(
            text=script,
            voice_id=state.get("tts_voice_id"),
            language="en",
        )
        result = await tts_engine.generate_speech(request)

        content_value = result.audio_url
        if not content_value and result.audio_data:
            # Save audio bytes to persistent temp file for downstream mixing
            content_value = _save_to_temp(
                result.audio_data, ".mp3", "opensns_tts_", state.get("campaign_id", 0)
            )

        if content_value:
            from app.services.agents.state import GeneratedAudioAsset

            tts_asset = GeneratedAudioAsset(
                asset_type="tts",
                content=content_value,
                metadata={
                    "engine": state.get("default_tts_engine", "openai-tts"),
                    "voice_id": state.get("tts_voice_id"),
                    "script_preview": script[:100],
                    "duration": result.duration,
                    **result.metadata,
                },
            )
            generated_tts.append(tts_asset)
        else:
            logger.warning("TTS generation returned no audio data")

    except Exception as e:
        logger.warning(f"TTS generation failed: {e}")

    return {
        "generated_tts": generated_tts,
        "tts_done": True,
        "current_step": "audio_mixing",
    }


async def bgm_generation_node(state: AgentState) -> dict[str, Any]:
    """Generate or select background music."""
    if not state.get("bgm_enabled", False):
        return {
            "generated_bgm": [],
            "bgm_done": True,
            "current_step": "audio_mixing",
        }

    bgm_engine = _get_bgm_engine(state)
    generated_bgm = []

    if bgm_engine is None:
        logger.warning("No BGM engine available")
        return {
            "generated_bgm": [],
            "bgm_done": True,
            "current_step": "audio_mixing",
        }

    try:
        from app.services.audio.interfaces import MusicRequest

        request = MusicRequest(
            style=state.get("bgm_style"),
            duration=15.0,
        )
        result = await bgm_engine.generate_music(request)

        content_value = result.audio_url
        if not content_value and result.audio_data:
            # Save audio bytes to persistent temp file for downstream mixing
            content_value = _save_to_temp(
                result.audio_data, ".mp3", "opensns_bgm_", state.get("campaign_id", 0)
            )

        if content_value:
            from app.services.agents.state import GeneratedAudioAsset

            bgm_asset = GeneratedAudioAsset(
                asset_type="bgm",
                content=content_value,
                metadata={
                    "engine": state.get("default_bgm_engine", "static-bgm"),
                    "style": state.get("bgm_style"),
                    "duration": result.duration,
                    **result.metadata,
                },
            )
            generated_bgm.append(bgm_asset)
        else:
            logger.warning("BGM generation returned no audio data")

    except Exception as e:
        logger.warning(f"BGM generation failed: {e}")

    return {
        "generated_bgm": generated_bgm,
        "bgm_done": True,
        "current_step": "audio_mixing",
    }


async def audio_mixing_node(state: AgentState) -> dict[str, Any]:
    """Mix TTS narration and BGM into generated videos via TaskIQ worker.

    Writes to mixed_videos/mixed_ugc_videos, NOT generated_videos.
    Uses operator.add so results append rather than overwrite.
    Falls back to original unmixed video on any failure.
    """
    tts_list = state.get("generated_tts", [])
    bgm_list = state.get("generated_bgm", [])

    if not tts_list and not bgm_list:
        return {
            "mixed_videos": [],
            "mixed_ugc_videos": [],
            "audio_mixed": True,
            "current_step": "merge_branches",
        }

    narration_url = None
    bgm_url = None

    for tts in tts_list:
        if tts.content and tts.content != "tts_audio_data":
            narration_url = tts.content
            break

    for bgm in bgm_list:
        if bgm.content and bgm.content != "bgm_audio_data":
            bgm_url = bgm.content
            break

    # Audio assets are in-memory only (no URLs) — skip worker-based mixing
    if not narration_url and not bgm_url:
        logger.info("Audio assets are in-memory only, skipping worker-based mixing")
        return {
            "mixed_videos": [],
            "mixed_ugc_videos": [],
            "audio_mixed": True,
            "current_step": "merge_branches",
        }

    mixed_videos = []
    mixed_ugc_videos = []

    for video in state.get("generated_videos", []):
        if video.metadata.get("fallback", False):
            continue
        video_url = video.content
        if not video_url:
            continue

        campaign_id = state.get("campaign_id", 0)
        mixed_result = await _dispatch_mix_task(
            video_url, narration_url, bgm_url, campaign_id=campaign_id
        )
        if mixed_result:
            mixed_asset = GeneratedAsset(
                asset_type="video",
                content=mixed_result.get("video_url", video_url),
                platform=video.platform,
                metadata={
                    **video.metadata,
                    "audio_mixed": True,
                    "has_narration": narration_url is not None,
                    "has_bgm": bgm_url is not None,
                },
            )
            mixed_videos.append(mixed_asset)

    for ugc_video in state.get("generated_ugc_videos", []):
        if ugc_video.metadata.get("fallback", False):
            continue
        video_url = ugc_video.content
        if not video_url:
            continue

        # UGC videos already have voice — only add BGM
        campaign_id = state.get("campaign_id", 0)
        mixed_result = await _dispatch_mix_task(
            video_url,
            None,
            bgm_url,
            preserve_original_audio=True,
            campaign_id=campaign_id,
        )
        if mixed_result:
            mixed_asset = GeneratedAsset(
                asset_type="video",
                content=mixed_result.get("video_url", video_url),
                platform=ugc_video.platform,
                metadata={
                    **ugc_video.metadata,
                    "audio_mixed": True,
                    "has_bgm": bgm_url is not None,
                },
            )
            mixed_ugc_videos.append(mixed_asset)

    return {
        "mixed_videos": mixed_videos,
        "mixed_ugc_videos": mixed_ugc_videos,
        "audio_mixed": True,
        "current_step": "merge_branches",
    }


async def _dispatch_mix_task(
    video_url: str,
    narration_url: Optional[str],
    bgm_url: Optional[str],
    preserve_original_audio: bool = False,
    campaign_id: int = 0,
) -> Optional[dict]:
    """Dispatch audio mixing to TaskIQ worker if available, otherwise run directly.

    Returns mixed video info dict on success, None on failure.
    Falls back gracefully — never raises.
    """
    from app.services.audio.interfaces import AudioMixRequest

    spec = {
        "video_url": video_url,
        "narration_url": narration_url,
        "bgm_url": bgm_url,
        "narration_volume": 1.0,
        "bgm_volume": 0.15,
        "ducking_enabled": True,
        "preserve_original_audio": preserve_original_audio,
    }

    # Try TaskIQ worker first (requires Redis)
    try:
        from app.worker import mix_audio_task

        task = await mix_audio_task.kiq(spec)
        result = await task.wait_result(
            timeout=settings.AUDIO_MIX_TIMEOUT_SECONDS,
        )

        if result.is_err:
            logger.warning(f"Audio mix task failed: {result.error}")
            return None

        task_result = result.return_value
        if task_result and task_result.get("success"):
            return task_result

        logger.warning(f"Audio mix returned failure: {task_result}")
        return None

    except Exception as e:
        logger.info(f"TaskIQ unavailable ({e}), falling back to direct ffmpeg mixing")

    # Fallback: run ffmpeg directly (no Redis/worker needed)
    try:
        from app.services.audio.mixer import ffmpeg_mix_audio

        request = AudioMixRequest(**spec)
        result = await ffmpeg_mix_audio(request)

        if result.video_data:
            # Save mixed video to temp file and return URL
            mixed_path = _save_to_temp(
                result.video_data, ".mp4", "opensns_mixed_", campaign_id=campaign_id
            )
            return {
                "success": True,
                "video_url": mixed_path,
                "metadata": result.metadata,
            }

        logger.warning("Direct ffmpeg mixing produced no output")
        return None

    except Exception as e:
        logger.warning(f"Direct ffmpeg mixing failed: {e}")
        return None


async def merge_parallel_branches(state: AgentState) -> dict[str, Any]:
    return {
        "current_step": "platform_optimizer",
    }


async def platform_optimizer_node(state: AgentState) -> dict[str, Any]:
    optimized_assets: List[GeneratedAsset] = []

    for image in state.get("generated_images", []):
        for platform, spec in PLATFORM_SPECS.items():
            if platform == "tiktok":
                continue

            optimized_asset = GeneratedAsset(
                asset_type="image",
                content=image.content,
                platform=platform,
                metadata={
                    **image.metadata,
                    "optimized": True,
                    "requires_resize": True,
                    "original_content": image.content,
                    "target_width": spec["width"],
                    "target_height": spec["height"],
                    "aspect_ratio": spec["aspect_ratio"],
                },
            )
            optimized_assets.append(optimized_asset)

    for video in state.get("generated_videos", []):
        for platform in ["tiktok", "instagram_story"]:
            spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["tiktok"])
            optimized_asset = GeneratedAsset(
                asset_type="video",
                content=video.content,
                platform=platform,
                metadata={
                    **video.metadata,
                    "optimized": True,
                    "requires_resize": True,
                    "original_content": video.content,
                    "target_width": spec["width"],
                    "target_height": spec["height"],
                    "aspect_ratio": spec["aspect_ratio"],
                },
            )
            optimized_assets.append(optimized_asset)

    return {
        "optimized_assets": optimized_assets,
        "current_step": "performance_predictor",
    }


async def performance_predictor_node(state: AgentState) -> dict[str, Any]:
    llm = _get_llm_engine(state)
    predictions: List[PerformancePrediction] = []

    assets_to_predict = []
    for idx, copy in enumerate(state.get("generated_copies", [])):
        assets_to_predict.append(
            {
                "id": f"copy_{idx}",
                "type": "copy",
                "platform": copy.platform,
                "content": f"{copy.headline} - {copy.body}",
            }
        )
    for idx, img in enumerate(state.get("generated_images", [])):
        assets_to_predict.append(
            {
                "id": f"image_{idx}",
                "type": "image",
                "platform": img.platform,
                "content": img.metadata.get("prompt", ""),
            }
        )

    prompt = f"""Predict performance metrics for the following marketing assets.

Product Context:
{state.get("product_context", "No context available")}

Assets:
{json.dumps(assets_to_predict, indent=2)}

For each asset, predict:
- CTR (click-through rate): typical range 0.5% - 5%
- Engagement rate: typical range 1% - 10%
- Confidence in prediction: 0.0 - 1.0

Return a JSON object:
{{
    "predictions": [
        {{
            "asset_id": "copy_0",
            "platform": "instagram",
            "predicted_ctr": 0.025,
            "predicted_engagement_rate": 0.05,
            "confidence": 0.7,
            "recommendations": ["Consider adding urgency", "Test different CTA"]
        }}
    ]
}}"""

    try:
        response = await llm.generate_text(prompt)
        parsed = _extract_json(response)
        for p in parsed.get("predictions", []):
            predictions.append(
                PerformancePrediction(
                    asset_id=p.get("asset_id", "unknown"),
                    platform=p.get("platform", "unknown"),
                    predicted_ctr=p.get("predicted_ctr", 0.02),
                    predicted_engagement_rate=p.get("predicted_engagement_rate", 0.05),
                    confidence=p.get("confidence", 0.5),
                    recommendations=p.get("recommendations", []),
                )
            )
    except Exception as e:
        logger.warning(f"Performance prediction failed: {e}. Using defaults.")
        for asset in assets_to_predict:
            predictions.append(
                PerformancePrediction(
                    asset_id=asset["id"],
                    platform=asset["platform"],
                    predicted_ctr=0.02,
                    predicted_engagement_rate=0.05,
                    confidence=0.3,
                    recommendations=["Manual review recommended"],
                )
            )

    return {
        "performance_predictions": predictions,
        "current_step": "verification",
    }


async def verification_node(state: AgentState) -> dict[str, Any]:
    llm = _get_llm_engine(state)
    verification_results: List[VerificationResult] = []

    all_content = []
    for idx, copy in enumerate(state.get("generated_copies", [])):
        all_content.append(
            f"Copy #{idx + 1} ({copy.platform}): {copy.headline} - {copy.body}"
        )
    for idx, img in enumerate(state.get("generated_images", [])):
        all_content.append(
            f"Image #{idx + 1}: {img.metadata.get('angle', 'unknown')} - {img.content}"
        )

    prompt = f"""Review the following marketing content for quality and brand safety.

Content to review:
{chr(10).join(all_content)}

Product Context:
{state.get("product_context", "No context available")}

Evaluate:
1. Brand safety (no offensive, discriminatory, or misleading content)
2. Message clarity and professionalism
3. Call-to-action effectiveness
4. Target audience alignment
5. Consistency across platforms

Verification policy:
- Mentioning competitive advantages or product differentiation is ACCEPTABLE.
- Only flag content that is offensive, discriminatory, factually false, or misleading.
- Minor stylistic issues should be listed as suggestions, NOT as failures.
- Set "passed" to false ONLY for serious brand safety or factual accuracy violations.

Return a JSON object:
{{
    "passed": true or false,
    "issues": ["list of serious issues only, empty if none"],
    "suggestions": ["list of improvement suggestions"],
    "confidence": 0.0 to 1.0,
    "failed_items": ["Copy #1", "Image #2"]
}}"""

    try:
        response = await llm.generate_text(prompt)
        parsed = _extract_json(response)
        overall_result = VerificationResult(
            passed=parsed.get("passed", True),
            issues=parsed.get("issues", []),
            suggestions=parsed.get("suggestions", []),
            confidence=parsed.get("confidence", 0.9),
            failed_items=parsed.get("failed_items", []),
        )
        verification_results.append(overall_result)
    except Exception as e:
        logger.warning(f"Verification via LLM failed: {e}. Using default pass.")
        verification_results.append(
            VerificationResult(
                passed=True,
                issues=[],
                suggestions=["LLM verification unavailable, manual review recommended"],
                confidence=0.5,
                failed_items=[],
            )
        )

    all_passed = all(r.passed for r in verification_results)

    if all_passed:
        return {
            "verification_results": verification_results,
            "verification_feedback": None,
            "failed_items": [],
            "current_step": "complete",
            "is_complete": True,
        }

    retry_count = state.get("retry_count", 0) + 1
    max_retries = state.get("max_retries", 2)

    failed_result = verification_results[0]
    feedback = (
        "; ".join(failed_result.issues)
        if failed_result.issues
        else "Quality standards not met"
    )
    failed_items = failed_result.failed_items

    if retry_count >= max_retries:
        logger.warning(
            f"Verification max retries ({max_retries}) reached. "
            f"Completing with warnings: {feedback}"
        )
        return {
            "verification_results": verification_results,
            "verification_feedback": feedback,
            "failed_items": failed_items,
            "current_step": "complete",
            "is_complete": True,
            "retry_count": retry_count,
        }

    return {
        "verification_results": verification_results,
        "verification_feedback": feedback,
        "failed_items": failed_items,
        "current_step": "copy_generation",
        "retry_count": retry_count,
        "copy_done": False,
        "visual_done": False,
    }


def should_retry(state: AgentState) -> str:
    if state.get("is_complete", False):
        return "complete"

    failed_verifications = [
        r for r in state.get("verification_results", []) if not r.passed
    ]

    if not failed_verifications:
        return "complete"

    if state.get("retry_count", 0) >= state.get("max_retries", 2):
        return "complete"

    return "retry"
