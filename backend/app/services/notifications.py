from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, update
from sqlmodel import Session, select

from app.models.models import Notification, NotificationType, utc_now


def create_notification(
    session: Session,
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> Notification:
    """Create a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def get_notifications(
    session: Session,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notification], int]:
    """Get notifications for a user with pagination. Returns (notifications, total_count)."""
    base_query = select(Notification).where(Notification.user_id == user_id)
    count_query = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)

    if unread_only:
        base_query = base_query.where(Notification.is_read == False)  # noqa: E712
        count_query = count_query.where(Notification.is_read == False)  # noqa: E712

    total = int(session.exec(count_query).one() or 0)
    notifications = session.exec(
        base_query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    ).all()

    return list(notifications), total


def get_unread_count(session: Session, user_id: int) -> int:
    """Get count of unread notifications."""
    result = session.exec(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)  # noqa: E712
    ).one()
    return int(result or 0)


def mark_as_read(session: Session, user_id: int, notification_id: int) -> Notification | None:
    """Mark a single notification as read."""
    notification = session.exec(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).first()
    if notification:
        notification.is_read = True
        notification.updated_at = utc_now()
        session.add(notification)
        session.commit()
        session.refresh(notification)
    return notification


def mark_all_as_read(session: Session, user_id: int) -> int:
    """Mark all notifications as read. Returns count of updated notifications."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)  # noqa: E712
        .values(is_read=True, updated_at=utc_now())
    )
    result = session.exec(stmt)
    session.commit()
    return result.rowcount


def delete_notification(session: Session, user_id: int, notification_id: int) -> bool:
    """Delete a notification. Returns True if deleted."""
    notification = session.exec(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).first()
    if notification:
        session.delete(notification)
        session.commit()
        return True
    return False
