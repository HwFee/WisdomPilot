"""
应用配置模块。

本模块使用 Pydantic Settings 库来管理应用的所有配置项。配置来源优先级：
    1. 环境变量（最高优先级）
    2. .env 文件
    3. 代码中的默认值（最低优先级）

配置内容包括：
    - 应用基础信息（名称、调试模式）
    - 数据库连接（SQLite + aiosqlite 异步驱动）
    - JWT 认证参数（密钥、算法、令牌过期时间）
    - AI 大模型配置（提供商、API Key、模型名称等）
    - 限流参数（认证接口每分钟请求上限）

设计要点：
    - 使用 ``lru_cache`` 缓存 Settings 实例，确保全局只创建一次（单例模式）
    - 使用 ``field_validator`` 对关键配置做启动时校验（如 SECRET_KEY 不能为空）
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用全局配置类。

    继承自 Pydantic 的 ``BaseSettings``，会自动从环境变量和 .env 文件中
    读取与字段名同名的配置项。所有字段都有默认值，即使不配置 .env 也能启动
    （但 SECRET_KEY 除外，它必须通过环境变量或 .env 提供且不少于 32 字符）。

    关键属性说明：
        - ``DATABASE_URL``: SQLAlchemy 异步数据库连接字符串，默认使用 SQLite
        - ``SECRET_KEY``: JWT 令牌签名密钥，启动时强制校验非空且不少于 32 字符
        - ``ALGORITHM``: JWT 签名算法，默认 HS256（HMAC-SHA256 对称加密）
        - ``AI_PROVIDER``: AI 大模型提供商，支持 deepseek / openai 等
    """

    # 应用基础配置
    APP_NAME: str = "WisdomPilot"       # 应用名称
    DEBUG: bool = False                 # 调试模式（开启后输出更详细的日志）

    # 数据库配置
    # 格式：dialect+driver://path，sqlite+aiosqlite 表示使用 SQLite 数据库 + aiosqlite 异步驱动
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/data.db"

    # JWT 认证配置
    SECRET_KEY: str = ""                                # 令牌签名密钥（必须配置，至少 32 字符）
    ALGORITHM: str = "HS256"                            # JWT 签名算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440             # 普通登录令牌有效期：1 天（1440 分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER: int = 10080   # "记住我"令牌有效期：7 天（10080 分钟）

    # AI 大模型独立模块配置
    AI_PROVIDER: str = "deepseek"                       # AI 提供商名称
    AI_API_KEY: str = ""                                # AI 提供商的 API 密钥
    AI_MODEL: str = "deepseek-v4-flash"                 # 使用的模型名称
    AI_TEMPERATURE: float = 0.7                         # 生成温度（0-2，越高越随机）
    AI_BASE_URL: str | None = "https://api.deepseek.com"  # AI API 基础 URL
    AI_LOCAL_FIRST: bool = False                        # 是否优先使用本地模型
    AI_LOCAL_BASE_URL: str | None = None                # 本地模型的基础 URL

    # 接口限流配置
    AUTH_RATE_PER_MINUTE: int = 10  # 认证接口每分钟最大请求数（防止暴力破解）

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_required(cls, v: str) -> str:
        """校验 SECRET_KEY 配置。

        SECRET_KEY 是 JWT 令牌签名的核心密钥，如果为空或太短，
        会导致令牌安全性不足，容易被暴力破解。因此在应用启动时
        就直接报错，而不是等到运行时才发现。

        Args:
            v: 从环境变量/.env 读取到的 SECRET_KEY 值

        Returns:
            校验通过的 SECRET_KEY 原值

        Raises:
            ValueError: 当 SECRET_KEY 为空或长度不足 32 字符时
        """
        if not v:
            raise ValueError("SECRET_KEY is required and must not be empty")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_required(cls, v: str) -> str:
        """校验 DATABASE_URL 配置。

        确保数据库连接字符串不为空，防止应用在无数据库连接的情况下启动。

        Args:
            v: 从环境变量/.env 读取到的 DATABASE_URL 值

        Returns:
            校验通过的 DATABASE_URL 原值

        Raises:
            ValueError: 当 DATABASE_URL 为空时
        """
        if not v:
            raise ValueError("DATABASE_URL is required and must not be empty")
        return v

    # Pydantic Settings 配置：指定 .env 文件路径和大小写敏感性
    model_config = SettingsConfigDict(
        env_file=".env",          # 从项目根目录的 .env 文件读取配置
        case_sensitive=True,      # 环境变量名大小写敏感（SECRET_KEY != secret_key）
    )


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置的单例实例。

    使用 ``functools.lru_cache`` 装饰器实现单例模式：第一次调用时创建
    Settings 实例（从环境变量和 .env 文件加载），后续调用直接返回缓存的
    实例。这样既保证了全局配置一致性，又避免了重复读取环境变量的开销。

    Returns:
        Settings: 全局唯一的配置实例
    """
    return Settings()
