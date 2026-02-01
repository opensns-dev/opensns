import json
import logging
import re
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
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


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

    research_data = await research_service.scrape_url(state.get("product_url", ""))

    features_str = ", ".join(research_data.get("features", []))
    images_str = ", ".join(research_data.get("images", [])[:3])

    product_context = f"""
    Title: {research_data.get("title", "Unknown")}
    Description: {research_data.get("description", "No description")}
    Features: {features_str or "Not available"}
    Price: {research_data.get("price") or "Not available"}
    Images: {images_str or "Not available"}
    Content: {research_data.get("content", "")[:1500]}
    Source: {research_data.get("source", "unknown")}
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
Each angle should have a unique perspective for advertising.

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

Generate exactly 3 angles with different approaches that leverage our competitive advantages."""

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

    for angle in state.get("angles", []):
        prompt = f"""Generate ad copy for each of these platforms: {", ".join(platforms)}

Marketing Angle: {angle.angle_title}
Description: {angle.description}
Target Audience: {angle.target_persona}

Product Context:
{state.get("product_context", "No context available")}
{feedback_context}

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

Generate one copy for each platform: {", ".join(platforms)}."""

        try:
            response = await llm.generate_text(prompt)
            parsed = _extract_json(response)
            copies = [AdCopy(**c) for c in parsed.get("copies", [])]
            generated_copies.extend(copies)
        except Exception as e:
            logger.warning(
                f"Failed to generate copy for {angle.angle_title}: {e}. Using template."
            )
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
                f"clean modern background, studio lighting, commercial quality{prompt_suffix}"
            )

            creative = AdCreative(
                title=angle.angle_title,
                body=angle.description,
                platform="instagram",
                image_prompt=image_prompt,
            )

            source_image = (
                product_image if has_product_image else _get_default_image_bytes()
            )
            result = await image_engine.generate_ad_image(source_image, creative)

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
            result = await video_engine.image_to_video(
                image_url=image.content,
                motion_prompt="Smooth camera pan, product showcase, professional advertisement",
                duration=5.0,
            )

            video_asset = GeneratedAsset(
                asset_type="video",
                content=result.video_url or "generated_video_data",
                platform="tiktok",
                metadata={
                    "source_image": image.content,
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
1. Brand safety (no offensive content)
2. Message clarity
3. Call-to-action effectiveness
4. Target audience alignment
5. Consistency across platforms

Return a JSON object:
{{
    "passed": true or false,
    "issues": ["list of specific issues found, empty if none"],
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
    max_retries = state.get("max_retries", 3)

    failed_result = verification_results[0]
    feedback = (
        "; ".join(failed_result.issues)
        if failed_result.issues
        else "Quality standards not met"
    )
    failed_items = failed_result.failed_items

    if retry_count >= max_retries:
        return {
            "verification_results": verification_results,
            "verification_feedback": feedback,
            "failed_items": failed_items,
            "current_step": "complete",
            "is_complete": True,
            "retry_count": retry_count,
            "error": f"Max retries reached. Issues: {feedback}",
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

    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return "complete"

    return "retry"
