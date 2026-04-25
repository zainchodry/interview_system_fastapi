from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Company ──────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    website: str | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    website: str | None = None
    created_by: int


# ── Job ──────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    location: str | None = None
    salary: str | None = None
    job_type: Literal["full-time", "part-time", "contract", "remote"]
    company_id: int


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    location: str | None = None
    salary: str | None = None
    job_type: str
    is_active: bool
    created_at: datetime | None = None
    company_id: int
    created_by: int


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    salary: str | None = None
    job_type: Literal["full-time", "part-time", "contract", "remote"] | None = None
    is_active: bool | None = None


# ── Application ──────────────────────────────────────────────────

class JobApplicationCreate(BaseModel):
    job_id: int
    resume: str | None = None
    cover_letter: str | None = None


class JobApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_id: int
    status: str
    applied_at: datetime | None = None


class ApplicationStatusUpdate(BaseModel):
    status: Literal["applied", "shortlisted", "rejected", "hired"]