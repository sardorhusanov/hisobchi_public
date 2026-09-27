from functools import lru_cache
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    bot_token: str = ""
    database_url: str = "postgresql+asyncpg://localhost/work_management"
    database_pool_size: int = Field(default=2, ge=1, le=20)
    database_max_overflow: int = Field(default=1, ge=0, le=20)
    app_env: str = "development"
    log_level: str = "INFO"
    timezone: str = "Asia/Tashkent"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    mini_app_url: str = ""
    dev_telegram_user_id: int | None = None
    telegram_auth_max_age: int = Field(default=3600, ge=60, le=86400)

    @field_validator("dev_telegram_user_id", mode="before")
    @classmethod
    def optional_dev_id(cls, value):
        return None if value == "" else value

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @model_validator(mode="after")
    def secure_configuration(self):
        if self.dev_telegram_user_id is not None and not 0 < self.dev_telegram_user_id < 2**63:
            raise ValueError("DEV_TELEGRAM_USER_ID must be a positive Telegram ID")
        if "*" in self.allowed_origins:
            raise ValueError("CORS_ORIGINS must contain explicit origins")
        if self.mini_app_url and (
            urlparse(self.mini_app_url).scheme != "https" or not urlparse(self.mini_app_url).netloc
        ):
            raise ValueError("MINI_APP_URL must be an HTTPS URL")
        if self.app_env == "production":
            if not self.bot_token:
                raise ValueError("BOT_TOKEN is required in production")
            if any(urlparse(origin).scheme != "https" for origin in self.allowed_origins):
                raise ValueError("Production CORS origins must use HTTPS")
        return self

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        ZoneInfo(value)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
