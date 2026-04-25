from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict


# ── Slot ─────────────────────────────────────────────────────────

class SlotCreate(BaseModel):
    date: date
    start_time: time
    end_time: time


class SlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interviewer_id: int
    date: date
    start_time: time
    end_time: time
    is_booked: bool


# ── Interview ────────────────────────────────────────────────────

class InterviewCreate(BaseModel):
    application_id: int
    slot_id: int
    meeting_link: str | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    recruiter_id: int
    interviewer_id: int
    slot_id: int
    status: str
    meeting_link: str | None = None
    feedback: str | None = None
    created_at: datetime | None = None


# ── Response Action ──────────────────────────────────────────────

class InterviewAction(BaseModel):
    action: Literal["accept", "reject"]


# ── Feedback ─────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    feedback: str