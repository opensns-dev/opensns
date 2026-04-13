import json
from calendar import monthrange
from datetime import datetime, UTC
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel as PydanticBaseModel
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    CalendarView,
    Campaign,
    ScheduledPost,
    ScheduledPostCreate,
    ScheduledPostResponse,
    ScheduledPostUpdate,
    ScheduleStatus,
    User,
)

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


def _to_response(post: ScheduledPost) -> ScheduledPostResponse:
    return ScheduledPostResponse(
        id=post.id,  # type: ignore[arg-type]
        campaign_id=post.campaign_id,
        platform=post.platform,
        publish_connection_id=post.publish_connection_id,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        status=post.status,
        recurrence=post.recurrence,
        asset_ids=json.loads(post.asset_ids),
        copy_text=post.copy_text,
        error=post.error,
        created_at=post.created_at,
    )


@router.get("", response_model=List[ScheduledPostResponse])
@limiter.limit("60/minute")
async def list_scheduled_posts(
    request: Request,
    status: Optional[ScheduleStatus] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    stmt = select(ScheduledPost).where(ScheduledPost.user_id == current_user.id)
    if status is not None:
        stmt = stmt.where(ScheduledPost.status == status)
    if platform is not None:
        stmt = stmt.where(ScheduledPost.platform == platform)
    if from_date is not None:
        stmt = stmt.where(ScheduledPost.scheduled_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(ScheduledPost.scheduled_at <= to_date)
    stmt = stmt.order_by(ScheduledPost.scheduled_at.asc())  # type: ignore[union-attr]

    posts = session.exec(stmt).all()
    return [_to_response(p) for p in posts]


@router.get("/calendar", response_model=CalendarView)
@limiter.limit("60/minute")
async def get_calendar_view(
    request: Request,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _, last_day = monthrange(year, month)
    start = datetime(year, month, 1, tzinfo=UTC)
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)

    posts = session.exec(
        select(ScheduledPost)
        .where(
            ScheduledPost.user_id == current_user.id,
            ScheduledPost.scheduled_at >= start,
            ScheduledPost.scheduled_at <= end,
        )
        .order_by(ScheduledPost.scheduled_at.asc())  # type: ignore[union-attr]
    ).all()

    post_responses = [_to_response(p) for p in posts]
    return CalendarView(
        month=month,
        year=year,
        posts=post_responses,
        total_scheduled=sum(
            1
            for p in posts
            if p.status in (ScheduleStatus.PENDING, ScheduleStatus.SCHEDULED)
        ),
        total_published=sum(1 for p in posts if p.status == ScheduleStatus.PUBLISHED),
        total_failed=sum(1 for p in posts if p.status == ScheduleStatus.FAILED),
    )


@router.post("", response_model=ScheduledPostResponse)
@limiter.limit("20/minute")
async def create_scheduled_post(
    request: Request,
    data: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    campaign = session.exec(
        select(Campaign).where(
            Campaign.id == data.campaign_id,
            Campaign.user_id == current_user.id,
        )
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if data.scheduled_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=400, detail="scheduled_at must be in the future"
        )

    post = ScheduledPost(
        campaign_id=data.campaign_id,
        user_id=current_user.id,  # type: ignore[arg-type]
        platform=data.platform,
        publish_connection_id=data.publish_connection_id,
        scheduled_at=data.scheduled_at,
        status=ScheduleStatus.SCHEDULED,
        recurrence=data.recurrence,
        asset_ids=json.dumps(data.asset_ids or []),
        copy_text=data.copy_text,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return _to_response(post)


@router.put("/{post_id}", response_model=ScheduledPostResponse)
@limiter.limit("20/minute")
async def update_scheduled_post(
    request: Request,
    post_id: int,
    data: ScheduledPostUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    post = session.exec(
        select(ScheduledPost).where(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id,
        )
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status not in (ScheduleStatus.PENDING, ScheduleStatus.SCHEDULED):
        raise HTTPException(
            status_code=400,
            detail="Can only update posts with PENDING or SCHEDULED status",
        )

    if data.scheduled_at is not None:
        post.scheduled_at = data.scheduled_at
    if data.platform is not None:
        post.platform = data.platform
    if data.recurrence is not None:
        post.recurrence = data.recurrence
    if data.asset_ids is not None:
        post.asset_ids = json.dumps(data.asset_ids)
    if data.copy_text is not None:
        post.copy_text = data.copy_text
    if data.status is not None:
        post.status = data.status
    post.updated_at = datetime.now(UTC)

    session.add(post)
    session.commit()
    session.refresh(post)
    return _to_response(post)


@router.delete("/{post_id}")
@limiter.limit("20/minute")
async def cancel_scheduled_post(
    request: Request,
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    post = session.exec(
        select(ScheduledPost).where(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id,
        )
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    post.status = ScheduleStatus.CANCELLED
    post.updated_at = datetime.now(UTC)
    session.add(post)
    session.commit()
    return {"message": "Scheduled post cancelled"}


class RescheduleRequest(PydanticBaseModel):
    scheduled_at: datetime


@router.post("/{post_id}/reschedule", response_model=ScheduledPostResponse)
@limiter.limit("20/minute")
async def reschedule_post(
    request: Request,
    post_id: int,
    data: RescheduleRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    post = session.exec(
        select(ScheduledPost).where(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id,
        )
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if data.scheduled_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=400, detail="scheduled_at must be in the future"
        )

    post.scheduled_at = data.scheduled_at
    post.status = ScheduleStatus.SCHEDULED
    post.updated_at = datetime.now(UTC)
    session.add(post)
    session.commit()
    session.refresh(post)
    return _to_response(post)
