from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationResponse
from app.utils.deps import CurrentUser

router = APIRouter(prefix="/notifications", tags=["Notifications"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[NotificationResponse])
def my_notifications(db: DbSession, current_user: CurrentUser):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/unread-count")
def unread_count(db: DbSession, current_user: CurrentUser):
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .count()
    )
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=MessageResponse)
def mark_as_read(notification_id: int, db: DbSession, current_user: CurrentUser):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    db.commit()
    return MessageResponse(message="Marked as read")


@router.patch("/read-all", response_model=MessageResponse)
def mark_all_as_read(db: DbSession, current_user: CurrentUser):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return MessageResponse(message="All notifications marked as read")
