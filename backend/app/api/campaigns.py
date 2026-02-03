from typing import List
import io
import json
import logging
import zipfile
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import httpx
from app.db import get_session
from app.models.models import Campaign, CampaignStatus, CampaignCreate, User, Asset
from app.services.pipeline import run_campaign_pipeline, approve_and_resume
from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.services.usage import check_image_credits

logger = logging.getLogger(__name__)

# Security: Allowed hosts for asset URLs (SSRF prevention)
# Add your CDN/storage domains here
ALLOWED_ASSET_HOSTS = {
    "fal.media",
    "v3.fal.media",
    "storage.googleapis.com",
    "s3.amazonaws.com",
    "cdn.openai.com",
    "oaidalleapiprodscus.blob.core.windows.net",
    "replicate.delivery",
    "localhost",
    "127.0.0.1",
}

# Security: Maximum file size for export (50MB per asset)
MAX_ASSET_SIZE_BYTES = 50 * 1024 * 1024


def is_allowed_asset_url(url: str) -> bool:
    """Validate that asset URL is from an allowed host (SSRF prevention)."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        # Check exact match or subdomain match
        return any(
            hostname == allowed or hostname.endswith(f".{allowed}")
            for allowed in ALLOWED_ASSET_HOSTS
        )
    except Exception:
        return False


router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("/", response_model=Campaign)
async def create_campaign(
    campaign_in: CampaignCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    check_image_credits(session, current_user, 3)

    campaign = Campaign(
        **campaign_in.model_dump(),
        user_id=current_user.id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    background_tasks.add_task(run_campaign_pipeline, campaign.id)

    return campaign


@router.post("/{campaign_id}/approve", response_model=Campaign)
async def approve_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != CampaignStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail="Campaign is not awaiting approval")

    background_tasks.add_task(approve_and_resume, campaign_id)

    return campaign


@router.get("/", response_model=List[Campaign])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaigns = session.exec(
        select(Campaign).where(Campaign.user_id == current_user.id)
    ).all()
    return campaigns


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    session.delete(campaign)
    session.commit()
    return {"message": "Campaign deleted successfully"}


@router.get("/{campaign_id}/export")
@limiter.limit("5/minute")
async def export_campaign(
    request: Request,
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Export all campaign assets as a ZIP file."""
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == campaign_id, Campaign.user_id == current_user.id
        )
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get all assets for this campaign
    assets = session.exec(select(Asset).where(Asset.campaign_id == campaign_id)).all()

    if not assets:
        raise HTTPException(status_code=404, detail="No assets found for this campaign")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    skipped_assets = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for asset in assets:
            meta = json.loads(asset.asset_metadata or "{}")
            platform = meta.get("platform", "unknown")
            angle = meta.get("angle", str(asset.id))

            if asset.type == "COPY":
                # Text assets - write content directly
                filename = f"copy/{platform}_{angle}_{asset.id}.txt"
                content = f"Platform: {platform}\nAngle: {angle}\n\n{asset.content}"
                if meta.get("headline"):
                    content = f"Headline: {meta['headline']}\n{content}"
                if meta.get("cta"):
                    content = f"{content}\n\nCTA: {meta['cta']}"
                zf.writestr(filename, content)

            elif asset.type in ("IMAGE", "VIDEO"):
                # Security: Validate URL before fetching (SSRF prevention)
                if not is_allowed_asset_url(asset.content):
                    logger.warning(
                        f"Skipping asset {asset.id}: URL not in allowlist: {asset.content}"
                    )
                    skipped_assets.append({"id": asset.id, "reason": "URL not allowed"})
                    continue

                # Binary assets - download and add to ZIP
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        # Use streaming to check size before downloading fully
                        async with client.stream("GET", asset.content) as resp:
                            if resp.status_code != 200:
                                skipped_assets.append(
                                    {
                                        "id": asset.id,
                                        "reason": f"HTTP {resp.status_code}",
                                    }
                                )
                                continue

                            # Check Content-Length if available
                            content_length = resp.headers.get("content-length")
                            if (
                                content_length
                                and int(content_length) > MAX_ASSET_SIZE_BYTES
                            ):
                                logger.warning(
                                    f"Skipping asset {asset.id}: too large ({content_length} bytes)"
                                )
                                skipped_assets.append(
                                    {"id": asset.id, "reason": "File too large"}
                                )
                                continue

                            # Read with size limit
                            chunks = []
                            total_size = 0
                            async for chunk in resp.aiter_bytes():
                                total_size += len(chunk)
                                if total_size > MAX_ASSET_SIZE_BYTES:
                                    logger.warning(
                                        f"Skipping asset {asset.id}: exceeded size limit during download"
                                    )
                                    skipped_assets.append(
                                        {"id": asset.id, "reason": "File too large"}
                                    )
                                    break
                                chunks.append(chunk)
                            else:
                                # Successfully downloaded
                                content = b"".join(chunks)
                                ext = "mp4" if asset.type == "VIDEO" else "png"
                                folder = asset.type.lower()
                                filename = (
                                    f"{folder}/{platform}_{angle}_{asset.id}.{ext}"
                                )
                                zf.writestr(filename, content)

                except httpx.TimeoutException:
                    logger.warning(f"Timeout downloading asset {asset.id}")
                    skipped_assets.append({"id": asset.id, "reason": "Timeout"})
                except Exception as e:
                    logger.error(f"Error downloading asset {asset.id}: {e}")
                    skipped_assets.append({"id": asset.id, "reason": str(e)[:50]})

        # Add manifest file with export info
        manifest = {
            "campaign_id": campaign_id,
            "campaign_title": campaign.title,
            "total_assets": len(assets),
            "exported_assets": len(assets) - len(skipped_assets),
            "skipped_assets": skipped_assets,
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="campaign_{campaign_id}_assets.zip"'
        },
    )
