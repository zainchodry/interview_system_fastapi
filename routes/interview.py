from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview, InterviewSlot
from app.models.job import JobApplication
from app.models.notification import Notification
from app.schemas.common import MessageResponse
from app.schemas.interview import (
    FeedbackCreate,
    InterviewAction,
    InterviewCreate,
    InterviewResponse,
    SlotCreate,
    SlotResponse,
)
from app.utils.deps import CurrentUser, require_role

router = APIRouter(prefix="/interviews", tags=["Interviews"])

DbSession = Annotated[Session, Depends(get_db)]


# ══════════════════════════ SLOTS ════════════════════════════════

@router.post("/slot", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(
    data: SlotCreate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )

    slot = InterviewSlot(**data.model_dump(), interviewer_id=user.id)
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.get("/slots", response_model=list[SlotResponse])
def available_slots(db: DbSession):
    return (
        db.query(InterviewSlot)
        .filter(InterviewSlot.is_booked == False)  # noqa: E712
        .order_by(InterviewSlot.date, InterviewSlot.start_time)
        .all()
    )


@router.delete("/slot/{slot_id}", response_model=MessageResponse)
def delete_slot(
    slot_id: int,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    slot = db.query(InterviewSlot).filter(InterviewSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a booked slot")

    db.delete(slot)
    db.commit()
    return MessageResponse(message="Slot deleted")


# ══════════════════════════ SCHEDULE ════════════════════════════

@router.post("/schedule", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def schedule_interview(
    data: InterviewCreate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    slot = db.query(InterviewSlot).filter(InterviewSlot.id == data.slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot already booked")

    application = db.query(JobApplication).filter(JobApplication.id == data.application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    interview = Interview(
        application_id=application.id,
        recruiter_id=user.id,
        interviewer_id=slot.interviewer_id,
        slot_id=slot.id,
        meeting_link=data.meeting_link,
    )
    slot.is_booked = True

    db.add(interview)
    db.flush()

    # Notify the candidate
    db.add(Notification(
        user_id=application.candidate_id,
        message=f"Your interview for application #{application.id} has been scheduled",
        type="interview_scheduled",
    ))

    db.commit()
    db.refresh(interview)
    return interview


# ══════════════════════════ RESPONSE ════════════════════════════

@router.post("/response/{interview_id}", response_model=MessageResponse)
def respond_to_interview(
    interview_id: int,
    data: InterviewAction,
    db: DbSession,
    current_user: CurrentUser,
):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    new_status = "accepted" if data.action == "accept" else "rejected"
    interview.status = new_status

    # Notify the recruiter
    db.add(Notification(
        user_id=interview.recruiter_id,
        message=f"Interview #{interview.id} has been {new_status}",
        type="status_change",
    ))

    db.commit()
    return MessageResponse(message=f"Interview {new_status}")


# ══════════════════════════ MY INTERVIEWS ═══════════════════════

@router.get("/my", response_model=list[InterviewResponse])
def my_interviews(db: DbSession, current_user: CurrentUser):
    if current_user.role == "candidate":
        return (
            db.query(Interview)
            .join(JobApplication)
            .filter(JobApplication.candidate_id == current_user.id)
            .order_by(Interview.created_at.desc())
            .all()
        )
    elif current_user.role == "recruiter":
        return (
            db.query(Interview)
            .filter(Interview.recruiter_id == current_user.id)
            .order_by(Interview.created_at.desc())
            .all()
        )
    else:
        # admin or interviewer — see all assigned
        return (
            db.query(Interview)
            .filter(Interview.interviewer_id == current_user.id)
            .order_by(Interview.created_at.desc())
            .all()
        )


# ══════════════════════════ FEEDBACK ═══════════════════════════

@router.post("/feedback/{interview_id}", response_model=MessageResponse)
def add_feedback(
    interview_id: int,
    data: FeedbackCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    interview.feedback = data.feedback
    interview.status = "completed"

    # Notify candidate
    application = db.query(JobApplication).filter(JobApplication.id == interview.application_id).first()
    if application:
        db.add(Notification(
            user_id=application.candidate_id,
            message=f"Feedback received for interview #{interview.id}",
            type="status_change",
        ))

    db.commit()
    return MessageResponse(message="Feedback submitted and interview marked as completed")