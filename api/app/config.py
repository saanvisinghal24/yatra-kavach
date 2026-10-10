from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from pydantic import model_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Yatra Kavach"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PUBLIC_ORIGIN: str = "http://localhost:5173"
    DEMO_MODE: bool = False
    CONTACT_EMAIL: str = ""
    REVIEWED_BY: str = ""
    RETENTION_DAYS: int = 30

    @model_validator(mode="after")
    def production_guard(self):
        if self.ENVIRONMENT == "production":
            for key in ("SECRET_KEY", "QR_HMAC_SECRET", "JWT_SECRET"):
                value = getattr(self, key)
                if len(value) < 32 or any(x in value.lower() for x in ("secret", "default", "change", "example", "checkpoint-hmac", "jwt-staff")):
                    raise ValueError(f"{key} must be a unique random secret of at least 32 characters")
            if len({self.SECRET_KEY, self.QR_HMAC_SECRET, self.JWT_SECRET}) != 3:
                raise ValueError("Secrets must be distinct")
            if not self.PUBLIC_ORIGIN.startswith("https://") or "*" in self.PUBLIC_ORIGIN:
                raise ValueError("PUBLIC_ORIGIN must be your exact HTTPS origin")
            if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                raise ValueError("Production requires PostgreSQL")
            from urllib.parse import urlsplit, unquote
            if len(unquote(urlsplit(self.DATABASE_URL).password or '')) < 16:
                raise ValueError('Production database password must be at least 16 characters')
            if '<' in self.PUBLIC_ORIGIN or self.PUBLIC_ORIGIN.endswith('/'):
                raise ValueError('Set a real origin without a trailing slash')
            self.DEBUG = False
        return self

    # Database
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""

    # Security
    SECRET_KEY: str = ""
    QR_HMAC_SECRET: str = ""
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    # Notification & Alerting
    NOTIFIER_CHANNEL: str = "console"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Emergency Services
    CONTROL_ROOM_PHONE: str = ""
    SOS_FALLBACK_SMS_NUMBER: str = ""

    # External APIs
    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_CACHE_TTL_SECONDS: int = 1800

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
