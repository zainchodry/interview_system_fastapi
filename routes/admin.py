from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview
from app.models.job import Company, Job, JobApplication
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.utils.deps import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[object, Depends(require_role("admin"))]


# ── Dashboard Stats ──────────────────────────────────────────────

@router.get("/dashboard")
def admin_dashboard(db: DbSession, user: AdminUser):
    return {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active == True).count(),  # noqa: E712
        "total_companies": db.query(Company).count(),
        "total_jobs": db.query(Job).count(),
        "active_jobs": db.query(Job).filter(Job.is_active == True).count(),  # noqa: E712
        "total_applications": db.query(JobApplication).count(),
        "total_interviews": db.query(Interview).count(),
        "interviews_by_status": {
            "scheduled": db.query(Interview).filter(Interview.status == "scheduled").count(),
            "accepted": db.query(Interview).filter(Interview.status == "accepted").count(),
            "rejected": db.query(Interview).filter(Interview.status == "rejected").count(),
            "completed": db.query(Interview).filter(Interview.status == "completed").count(),
        },
    }


# ── User Management ─────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def list_users(db: DbSession, user: AdminUser):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/activate", response_model=MessageResponse)
def activate_user(user_id: int, db: DbSession, user: AdminUser):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    target.is_active = True
    db.commit()
    return MessageResponse(message=f"User '{target.username}' activated")


@router.patch("/users/{user_id}/deactivate", response_model=MessageResponse)
def deactivate_user(user_id: int, db: DbSession, user: AdminUser):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
    target.is_active = False
    db.commit()
    return MessageResponse(message=f"User '{target.username}' deactivated")
