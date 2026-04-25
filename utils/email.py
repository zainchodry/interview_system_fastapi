import logging
import random
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email via SMTP. Returns True on success, False on failure."""
    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        logger.warning("Email credentials not configured — skipping email send.")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USERNAME
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USERNAME, to_email, msg.as_string())
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp_email(email: str) -> str:
    """Generate and send an OTP. Returns the OTP string."""
    otp = generate_otp()
    send_email(email, "Password Reset OTP", f"Your OTP is: {otp}")
    return otp