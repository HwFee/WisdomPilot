from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "智码领航"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/data.db"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day (default)
    ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER: int = 10080  # 7 days (remember me)

    # AI Configuration (independent module)
    AI_PROVIDER: str = "deepseek"
    AI_API_KEY: str = ""
    AI_MODEL: str = "deepseek-v4-flash"
    AI_TEMPERATURE: float = 0.7
    AI_BASE_URL: str | None = "https://api.deepseek.com"
    AI_LOCAL_FIRST: bool = False
    AI_LOCAL_BASE_URL: str | None = None

    # MiniMax Configuration (for enhanced quiz generation)
    MINIMAX_API_KEY: str = ""
    MINIMAX_MODEL: str = "MiniMax-M2.7"

    # Embedding Configuration (for vector matching)
    EMBEDDING_PROVIDER: str = "siliconflow"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.siliconflow.cn/v1"
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_DIMENSIONS: int = 1024

    # External services
    JUDGE0_BASE_URL: str = "https://ce.judge0.com"

    # Rate limiting
    AUTH_RATE_PER_MINUTE: int = 10
    CODE_EXEC_RATE_PER_MINUTE: int = 30  # Reasonable limit for code execution

    # Test sandbox (disable in production)
    ENABLE_TEST_SANDBOX: bool = False

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
