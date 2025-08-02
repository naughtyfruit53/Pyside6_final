import os
from typing import Any, Dict, Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "TRITIQ ERP API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI migration of PySide6 ERP application"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database (Supabase PostgreSQL)
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Email Settings (Required for OTP)
    SMTP_HOST: str = "smtp.gmail.com"  # Changed back to SMTP_HOST to match .env
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None  # Gmail or SMTP user email
    SMTP_PASSWORD: Optional[str] = None  # Gmail app password or SMTP password  
    EMAILS_FROM_EMAIL: Optional[str] = None  # Sender email (same as SMTP_USERNAME)
    EMAILS_FROM_NAME: str = "TRITIQ ERP"
    
    # SendGrid (Alternative email service)
    SENDGRID_API_KEY: Optional[str] = None

    # Brevo (Sendinblue) Email Service - Primary
    BREVO_API_KEY: Optional[str] = None
    BREVO_FROM_EMAIL: Optional[str] = None
    BREVO_FROM_NAME: str = "TRITIQ ERP"
    
    # Redis (for caching and task queue)
    REDIS_URL: str = "redis://localhost:6379"
    
    # File Storage
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Cors
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Super Admin Configuration
    SUPER_ADMIN_EMAILS: List[str] = ["admin@tritiq.com", "superadmin@tritiq.com", "naughtyfruit53@gmail.com"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()