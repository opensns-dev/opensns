from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import Asset, AssetType
from app.core.registry import engine_registry

router = APIRouter(prefix="/videos", tags=["videos"])


class VideoGenerateRequest(BaseModel):
    image_url: str
    motion_prompt: Optional[str] = None
    duration: float = 5.0
    engine: str = "runway"  # runway, kling, cogvideox


class VideoGenerateResponse(BaseModel):
    task_id: str
    status: str
    video_url: Optional[str] = None


@router.get("/campaign/{campaign_id}", response_model=List[Asset])
async def list_videos(campaign_id: int, session: Session = Depends(get_session)):
    """List all video assets for a campaign."""
    videos = session.exec(
        select(Asset).where(
            Asset.campaign_id == campaign_id, Asset.type == AssetType.VIDEO
        )
    ).all()
    return videos


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: VideoGenerateRequest,
    background_tasks: BackgroundTasks,
):
    video_engine = engine_registry.get_video_engine_or_none(request.engine)
    if not video_engine:
        available = engine_registry.video_registry.list_engines()
        raise HTTPException(
            status_code=400,
            detail=f"Engine '{request.engine}' not found. Available: {available}",
        )

    import uuid

    task_id = str(uuid.uuid4())

    return VideoGenerateResponse(
        task_id=task_id,
        status="queued",
        video_url=None,
    )


@router.get("/status/{task_id}", response_model=VideoGenerateResponse)
async def get_video_status(task_id: str):
    """Check the status of a video generation task."""
    # In production, this would check the actual task status
    return VideoGenerateResponse(
        task_id=task_id,
        status="pending",
        video_url=None,
    )


@router.get("/engines")
async def list_engines():
    return {
        "engines": engine_registry.video_registry.list_engines(),
    }
