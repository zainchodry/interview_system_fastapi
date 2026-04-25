import logging
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine

# ── Import all models so they are registered with Base ───────────
from app.models import user, job, interview, notification  # noqa: F401

# ── Import routers ──────────────────────────────────────────────
from app.routes.auth import router as auth_router
from app.routes.job import router as job_router
from app.routes.interview import router as interview_router
from app.routes.profile import router as profile_router
from app.routes.admin import router as admin_router
from app.routes.notification import router as notification_router

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Create tables ────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── FastAPI App ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "A production-grade Interview Scheduling System API built with FastAPI. "
        "Features include JWT authentication, role-based access control, "
        "job management, interview scheduling, and real-time notifications."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──────────────────────────────────────────────
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Logging Middleware ───────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


# ── Global Exception Handler ────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


# ── Include Routers ─────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(job_router)
app.include_router(interview_router)
app.include_router(profile_router)
app.include_router(admin_router)
app.include_router(notification_router)


# ── Health Check ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
    }
