from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Profile
from app.schemas.common import MessageResponse
from app.schemas.user import ProfileResponse, ProfileUpdate
from app.utils.deps import CurrentUser

router = APIRouter(prefix="/profile", tags=["Profile"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=ProfileResponse)
def get_profile(current_user: CurrentUser, db: DbSession):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.put("/", response_model=MessageResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)

    db.commit()
    return MessageResponse(message="Profile updated successfully")
