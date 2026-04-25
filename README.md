# 🗓️ Interview Scheduling System

A **production-grade** Interview Scheduling System API built with **FastAPI**, featuring JWT authentication, role-based access control (RBAC), job management, interview scheduling with time-slot management, and real-time notifications.

---

## ✨ Features

| Category | Details |
|---|---|
| **Authentication** | JWT-based login/register, password change, OTP-based password reset |
| **Role-Based Access** | Three roles — `admin`, `recruiter`, `candidate` — with fine-grained permissions |
| **Job Management** | CRUD for companies & jobs, search/filter with pagination |
| **Applications** | Candidates apply for jobs; recruiters update application status |
| **Interview Scheduling** | Time-slot management, automated slot booking, meeting links |
| **Notifications** | In-app notifications for interview events with read/unread tracking |
| **Admin Dashboard** | Platform-wide stats, user activate/deactivate controls |
| **Security** | Env-based secrets, bcrypt password hashing, input validation |
| **Production Extras** | CORS, request logging, global error handler, health check |

---

## 🏗️ Architecture

```
app/
├── main.py                  # FastAPI app, middleware, routers
├── config.py                # Pydantic Settings (env-based)
├── database.py              # SQLAlchemy engine & session
├── models/
│   ├── user.py              # User, Profile, PasswordResetOTP
│   ├── job.py               # Company, Job, JobApplication
│   ├── interview.py         # InterviewSlot, Interview
│   └── notification.py      # Notification
├── schemas/
│   ├── common.py            # MessageResponse, PaginatedResponse
│   ├── user.py              # Auth & profile schemas
│   ├── job.py               # Job & application schemas
│   ├── interview.py         # Interview & slot schemas
│   └── notification.py      # Notification schema
├── routes/
│   ├── auth.py              # /auth/*
│   ├── job.py               # /jobs/*
│   ├── interview.py         # /interviews/*
│   ├── profile.py           # /profile/*
│   ├── admin.py             # /admin/*
│   └── notification.py      # /notifications/*
└── utils/
    ├── security.py          # JWT & password hashing
    ├── deps.py              # Dependency injection (auth, roles)
    └── email.py             # SMTP email & OTP
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd interview_scheduling_system_fastapi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` or edit `.env`:

```env
SQLALCHEMY_DATABASE_URI=sqlite:///app.db
SECRET_KEY=your-super-secret-key-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
CORS_ORIGINS=*
OTP_EXPIRE_MINUTES=10
```

### Run

```bash
# Development (with auto-reload)
fastapi dev

# Production
fastapi run
```

The API will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Endpoints

### Authentication (`/auth`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/auth/register` | Public | Register a new user |
| POST | `/auth/login` | Public | Login & get JWT token |
| POST | `/auth/change-password` | Authenticated | Change password |
| POST | `/auth/forgot-password` | Public | Send OTP to email |
| POST | `/auth/reset-password` | Public | Reset password with OTP |

### Jobs (`/jobs`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/jobs/company` | Recruiter/Admin | Create a company |
| GET | `/jobs/companies` | Public | List all companies |
| POST | `/jobs/` | Recruiter/Admin | Create a job posting |
| GET | `/jobs/` | Public | List jobs (paginated, searchable) |
| GET | `/jobs/{id}` | Public | Get job details |
| PATCH | `/jobs/{id}` | Owner/Admin | Update a job posting |
| DELETE | `/jobs/{id}` | Owner/Admin | Delete a job posting |
| POST | `/jobs/apply` | Candidate | Apply for a job |
| GET | `/jobs/my-applications` | Candidate | My applications |
| GET | `/jobs/applications/{job_id}` | Recruiter/Admin | Applications for a job |
| PATCH | `/jobs/update-status/{id}` | Recruiter/Admin | Update application status |

### Interviews (`/interviews`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/interviews/slot` | Recruiter/Admin | Create an interview slot |
| GET | `/interviews/slots` | Public | List available slots |
| DELETE | `/interviews/slot/{id}` | Recruiter/Admin | Delete an unbooked slot |
| POST | `/interviews/schedule` | Recruiter/Admin | Schedule an interview |
| POST | `/interviews/response/{id}` | Authenticated | Accept/reject interview |
| GET | `/interviews/my` | Authenticated | My interviews |
| POST | `/interviews/feedback/{id}` | Authenticated | Submit feedback |

### Profile (`/profile`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/profile/` | Authenticated | Get my profile |
| PUT | `/profile/` | Authenticated | Update my profile |

### Admin (`/admin`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/admin/dashboard` | Admin | Platform statistics |
| GET | `/admin/users` | Admin | List all users |
| PATCH | `/admin/users/{id}/activate` | Admin | Activate a user |
| PATCH | `/admin/users/{id}/deactivate` | Admin | Deactivate a user |

### Notifications (`/notifications`)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/notifications/` | Authenticated | My notifications |
| GET | `/notifications/unread-count` | Authenticated | Unread count |
| PATCH | `/notifications/{id}/read` | Authenticated | Mark as read |
| PATCH | `/notifications/read-all` | Authenticated | Mark all as read |

---

## 🔐 Roles & Permissions

| Role | Capabilities |
|------|-------------|
| **Admin** | Full access: manage users, view dashboard, manage all jobs/interviews |
| **Recruiter** | Create companies/jobs, manage applications, schedule interviews |
| **Candidate** | Apply for jobs, respond to interviews, view own applications |

---

## 🛠️ Tech Stack

- **FastAPI** — High-performance async web framework
- **SQLAlchemy 2.0** — ORM with modern `DeclarativeBase`
- **Pydantic V2** — Data validation with `ConfigDict`
- **python-jose** — JWT token handling
- **Passlib + bcrypt** — Secure password hashing
- **SQLite** — Default database (swap for PostgreSQL in production)

---

## 📄 License

This project is provided for educational and demonstration purposes.
