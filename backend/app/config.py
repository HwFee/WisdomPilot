import os
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "AIcodiingTeach"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI Configuration (independent module)
    AI_PROVIDER: str = "openai"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.7
    AI_BASE_URL: str | None = None

    # External services
    JUDGE0_BASE_URL: str = "https://ce.judge0.com"

    # Rate limiting
    AUTH_RATE_PER_MINUTE: int = 10
    CODE_EXEC_RATE_PER_MINUTE: int = 5

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_required(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY is required and must not be empty")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_required(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required and must not be empty")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
