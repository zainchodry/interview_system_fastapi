from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=ENV_PATH, env_file_encoding="utf-8")

    PROJECT_NAME: str = "Interview Scheduling System"
    PROJECT_VERSION: str = "1.0.0"

    # Database
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///app.db"

    # JWT
    SECRET_KEY: str = "change-me-to-a-random-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Email (SMTP)
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    # CORS
    CORS_ORIGINS: str = "*"

    # OTP
    OTP_EXPIRE_MINUTES: int = 10


settings = Settings()