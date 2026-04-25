import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Company, Job, JobApplication
from app.schemas.common import MessageResponse
from app.schemas.job import (
    ApplicationStatusUpdate,
    CompanyCreate,
    CompanyResponse,
    JobApplicationCreate,
    JobApplicationResponse,
    JobCreate,
    JobResponse,
    JobUpdate,
)
from app.utils.deps import CurrentUser, require_role

router = APIRouter(prefix="/jobs", tags=["Jobs"])

DbSession = Annotated[Session, Depends(get_db)]


# ══════════════════════════ COMPANY ══════════════════════════════

@router.post("/company", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    company = Company(**data.model_dump(), created_by=user.id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies", response_model=list[CompanyResponse])
def list_companies(db: DbSession):
    return db.query(Company).all()


# ══════════════════════════ JOB ══════════════════════════════════

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    # Validate company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    job = Job(**data.model_dump(), created_by=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/", response_model=dict)
def list_jobs(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    search: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
):
    query = db.query(Job).filter(Job.is_active == True)  # noqa: E712

    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [JobResponse.model_validate(j) for j in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: DbSession):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    data: JobUpdate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your job posting")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", response_model=MessageResponse)
def delete_job(
    job_id: int,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your job posting")

    db.delete(job)
    db.commit()
    return MessageResponse(message="Job deleted successfully")


# ══════════════════════════ APPLICATION ══════════════════════════

@router.post("/apply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def apply_job(
    data: JobApplicationCreate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("candidate"))],
):
    # Check job exists and is active
    job = db.query(Job).filter(Job.id == data.job_id, Job.is_active == True).first()  # noqa: E712
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or inactive")

    # Prevent duplicate applications
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == data.job_id,
        JobApplication.candidate_id == user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already applied")

    application = JobApplication(**data.model_dump(), candidate_id=user.id)
    db.add(application)
    db.commit()
    return MessageResponse(message="Applied successfully")


@router.get("/my-applications", response_model=list[JobApplicationResponse])
def my_applications(
    db: DbSession,
    user: Annotated[object, Depends(require_role("candidate"))],
):
    return (
        db.query(JobApplication)
        .filter(JobApplication.candidate_id == user.id)
        .order_by(JobApplication.applied_at.desc())
        .all()
    )


@router.get("/applications/{job_id}", response_model=list[JobApplicationResponse])
def job_applications(
    job_id: int,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    """List all applications for a specific job (recruiter/admin only)."""
    return (
        db.query(JobApplication)
        .filter(JobApplication.job_id == job_id)
        .order_by(JobApplication.applied_at.desc())
        .all()
    )


@router.patch("/update-status/{app_id}", response_model=MessageResponse)
def update_status(
    app_id: int,
    data: ApplicationStatusUpdate,
    db: DbSession,
    user: Annotated[object, Depends(require_role("recruiter", "admin"))],
):
    application = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.status = data.status
    db.commit()
    return MessageResponse(message=f"Status updated to '{data.status}'")
