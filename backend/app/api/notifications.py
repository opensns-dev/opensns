from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import NotificationResponse, User
from app.services.notifications import (
    delete_notification,
    get_notifications,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=dict)
@limiter.limit("60/minute")
async def list_notifications(
    request: Request,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List notifications with pagination."""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = current_user.id
    if limit > 100:
        limit = 100
    notifications, total = get_notifications(
        session, user_id, unread_only=unread_only, limit=limit, offset=offset
    )
    return {
        "notifications": [NotificationResponse.model_validate(n) for n in notifications],
        "total": total,
        "unread_count": get_unread_count(session, user_id),
    }


@router.get("/unread-count")
@limiter.limit("120/minute")
async def get_unread_notification_count(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get count of unread notifications."""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"count": get_unread_count(session, current_user.id)}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
@limiter.limit("60/minute")
async def mark_notification_read(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mark a notification as read."""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    notification = mark_as_read(session, current_user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/read-all")
@limiter.limit("30/minute")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Mark all notifications as read."""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    count = mark_all_as_read(session, current_user.id)
    return {"updated": count}


@router.delete("/{notification_id}")
@limiter.limit("60/minute")
async def delete_notification_endpoint(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete a notification."""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    deleted = delete_notification(session, current_user.id, notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}
