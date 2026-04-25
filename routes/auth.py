from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import PasswordResetOTP, Profile, User
from app.schemas.common import MessageResponse
from app.schemas.user import (
    ChangePassword,
    ForgotPassword,
    ResetPassword,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.config import settings
from app.utils.deps import CurrentUser
from app.utils.email import send_otp_email
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

DbSession = Annotated[Session, Depends(get_db)]


# ── Register ─────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: DbSession):
    # Check for duplicates
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    db.flush()  # get new_user.id

    db.add(Profile(user_id=new_user.id))
    db.commit()
    db.refresh(new_user)
    return new_user


# ── Login ────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: DbSession):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(data={"sub": db_user.email})
    return TokenResponse(access_token=token)


# ── Change Password ─────────────────────────────────────────────

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    data: ChangePassword,
    current_user: CurrentUser,
    db: DbSession,
):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )

    current_user.password = hash_password(data.new_password)
    db.commit()
    return MessageResponse(message="Password changed successfully")


# ── Forgot Password (send OTP) ──────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPassword, db: DbSession):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Don't reveal if email exists — always return success
        return MessageResponse(message="If the email exists, an OTP has been sent")

    # Invalidate old OTPs
    db.query(PasswordResetOTP).filter(
        PasswordResetOTP.user_id == user.id,
        PasswordResetOTP.is_used == False,
    ).update({"is_used": True})

    otp_code = send_otp_email(user.email)

    otp_record = PasswordResetOTP(
        user_id=user.id,
        otp=otp_code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(otp_record)
    db.commit()
    return MessageResponse(message="If the email exists, an OTP has been sent")


# ── Reset Password (verify OTP) ─────────────────────────────────

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPassword, db: DbSession):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    otp_record = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.otp == data.otp,
            PasswordResetOTP.is_used == False,
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    if otp_record.expires_at < datetime.now(timezone.utc):
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired",
        )

    # Apply new password
    user.password = hash_password(data.new_password)
    otp_record.is_used = True
    db.commit()
    return MessageResponse(message="Password reset successfully")
