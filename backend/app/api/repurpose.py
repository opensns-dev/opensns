import json
import re
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.db import get_session
from app.models.models import (
    CREDIT_COSTS,
    ContentPlatform,
    RepurposeContent,
    RepurposeContentResponse,
    RepurposeJob,
    RepurposeJobCreate,
    RepurposeJobResponse,
    User,
)
from app.services.repurpose.pipeline import run_repurpose_pipeline
from app.services.usage import check_credits

router = APIRouter(prefix="/repurpose", tags=["repurpose"])

YOUTUBE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w-]+"
)


def _job_to_response(job: RepurposeJob) -> RepurposeJobResponse:
    target_platforms = []
    try:
        target_platforms = json.loads(job.target_platforms)
    except (json.JSONDecodeError, TypeError):
        pass

    key_points = None
    if job.key_points:
        try:
            key_points = json.loads(job.key_points)
        except (json.JSONDecodeError, TypeError):
            pass

    return RepurposeJobResponse(
        id=job.id,
        youtube_url=job.youtube_url,
        video_title=job.video_title,
        video_duration=job.video_duration,
        status=job.status,
        tone_style=job.tone_style,
        target_platforms=target_platforms,
        transcript=job.transcript,
        summary=job.summary,
        key_points=key_points,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _content_to_response(content: RepurposeContent) -> RepurposeContentResponse:
    metadata = {}
    try:
        metadata = json.loads(content.content_metadata)
    except (json.JSONDecodeError, TypeError):
        pass

    return RepurposeContentResponse(
        id=content.id,
        job_id=content.job_id,
        platform=content.platform,
        content=content.content,
        content_metadata=metadata,
        created_at=content.created_at,
    )


@router.post("/", response_model=RepurposeJobResponse)
async def create_repurpose_job(
    job_in: RepurposeJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not YOUTUBE_URL_PATTERN.match(job_in.youtube_url):
        raise HTTPException(status_code=400, detail="유효한 YouTube URL이 아닙니다.")

    check_credits(session, current_user, CREDIT_COSTS["repurpose"])

    job = RepurposeJob(
        user_id=current_user.id,
        youtube_url=job_in.youtube_url,
        tone_style=job_in.tone_style,
        target_platforms=json.dumps([p.value for p in job_in.target_platforms]),
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    background_tasks.add_task(run_repurpose_pipeline, job.id)

    return _job_to_response(job)


@router.get("/", response_model=List[RepurposeJobResponse])
async def list_repurpose_jobs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    jobs = session.exec(
        select(RepurposeJob)
        .where(RepurposeJob.user_id == current_user.id)
        .order_by(RepurposeJob.created_at.desc())
    ).all()
    return [_job_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=RepurposeJobResponse)
async def get_repurpose_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    job = session.exec(
        select(RepurposeJob).where(
            RepurposeJob.id == job_id,
            RepurposeJob.user_id == current_user.id,
        )
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="리퍼포징 작업을 찾을 수 없습니다.")
    return _job_to_response(job)


@router.get("/{job_id}/contents", response_model=List[RepurposeContentResponse])
async def get_repurpose_contents(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    job = session.exec(
        select(RepurposeJob).where(
            RepurposeJob.id == job_id,
            RepurposeJob.user_id == current_user.id,
        )
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="리퍼포징 작업을 찾을 수 없습니다.")

    contents = session.exec(
        select(RepurposeContent).where(RepurposeContent.job_id == job_id)
    ).all()
    return [_content_to_response(c) for c in contents]


@router.delete("/{job_id}")
async def delete_repurpose_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    job = session.exec(
        select(RepurposeJob).where(
            RepurposeJob.id == job_id,
            RepurposeJob.user_id == current_user.id,
        )
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="리퍼포징 작업을 찾을 수 없습니다.")

    session.delete(job)
    session.commit()
    return {"message": "리퍼포징 작업이 삭제되었습니다."}
