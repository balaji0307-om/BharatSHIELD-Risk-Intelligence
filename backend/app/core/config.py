"""
Core application settings for BharatSHIELD backend.
Loads from environment variables or falls back to sensible defaults.
"""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "BharatSHIELD — Merchant Risk Intelligence"
    API_V1_STR: str = "/api"
    DEBUG: bool = True
    GEMINI_API_KEY: Optional[str] = None
    DEMO_MODE: bool = True
    
    # Security & Authentication
    JWT_SECRET_KEY: str = "bharatshield-super-secret-key-change-in-production-2025"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour for access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30    # 30 days for Remember Me
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5     # Lockout threshold
    LOCKOUT_MINUTES: int = 15              # Temporary account lockout duration

    # CAPTCHA Protection (Google reCAPTCHA v2/v3 or hCaptcha compatible)
    # Uses standard Google reCAPTCHA test keys by default; override in production via env
    RECAPTCHA_SECRET_KEY: str = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    RECAPTCHA_SITE_KEY: str = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    
    # Database (PostgreSQL primary with SQLite fallback)
    USE_SQLITE: bool = True
    SQLITE_URL: str = f"sqlite:///{BASE_DIR}/bharatshield.db"
    DATABASE_URL: Optional[str] = None
    
    @property
    def effective_db_url(self) -> str:
        if self.USE_SQLITE or not self.DATABASE_URL:
            return self.SQLITE_URL
        return self.DATABASE_URL
        
    # ML Model Artifacts
    MODEL_PATH: str = str(BASE_DIR / "ml" / "models" / "fraud_model.pkl")
    SCALER_PATH: str = str(BASE_DIR / "ml" / "models" / "scaler.pkl")
    FEATURE_CONFIG_PATH: str = str(BASE_DIR / "ml" / "models" / "feature_config.json")
    
    # Anomaly / Spike Detection Defaults
    SPIKE_WINDOW_MINUTES: int = 60
    SPIKE_ZSCORE_THRESHOLD: float = 2.0
    SPIKE_SUSPICIOUS_RATIO_THRESHOLD: float = 0.15
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
