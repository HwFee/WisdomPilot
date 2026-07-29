"""
应用启动与关闭生命周期管理模块。

本模块使用 FastAPI 的 ``lifespan`` 机制来管理应用启动和关闭时的资源初始化与清理。
相比旧的 ``@app.on_event("startup")`` 方式，lifespan 是 FastAPI 推荐的新方式，
它使用 ``asynccontextmanager`` 将启动和关闭逻辑封装在一起，更加清晰。

启动时执行的操作（按顺序）：
    1. 配置日志格式和级别
    2. 初始化数据库（建表 + 版本标记）
    3. 执行种子数据填充（确保系统有默认训练舱数据）
    4. 配置 AI 服务（初始化大模型提供商连接）

关闭时执行的操作：
    1. 关闭 AI 服务连接（释放 HTTP 客户端等资源）
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

# ---------------------------------------------------------------------------
# 模型注册导入（副作用导入）
# ---------------------------------------------------------------------------
# 这些 import 语句的唯一目的不是使用导入的内容，而是触发模型类的定义，
# 让 SQLAlchemy 将它们注册到 Base.metadata 中。如果不导入，init_db() 的
# create_all 就不知道要创建哪些表。
# noqa: F401 告诉 linter："我知道这个导入没被直接使用，但它是必须的"
from app.auth import models as _register_auth_models  # noqa: F401 - register User into Base.metadata
from app.training import models as _register_training_models  # noqa: F401 - register training models before init_db
from app.config import Settings

# 显式标记副作用导入：两个模块都只为了让模型注册到 Base.metadata
# Explicit side-effect imports: both exist solely to register models into Base.metadata before table creation.
_MODELS_REGISTERED = (_register_auth_models, _register_training_models)
from app.database import AsyncSessionLocal, init_db
from app.training.seed import seed_deck
from app.ai.config import AIProviderConfig
from app.ai.service import ai_service

# 日志格式：时间 - 模块名 - 级别 - 消息
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# 应用服务层日志记录器名称
APP_SERVICES_LOGGER = "app.services"


def configure_logging() -> None:
    """配置应用日志（仅在启动时执行一次）。

    设置根日志级别为 INFO，并为 ``app.services`` 包设置独立的日志级别。
    日志格式为：``2026-07-28 10:00:00 - app.main - INFO - 消息内容``
    """
    """Configure application logging once during startup."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logging.getLogger(APP_SERVICES_LOGGER).setLevel(logging.INFO)


def configure_ai_service(settings: Settings) -> None:
    """从应用配置中初始化 AI 服务提供商。

    将 Settings 中的 AI 相关配置项转换为 AIProviderConfig 对象，
    然后传递给全局的 ai_service 实例进行初始化。这样 AI 服务就
    可以在应用运行期间使用配置好的大模型进行对话生成。

    Args:
        settings: 应用全局配置实例，包含 AI_PROVIDER、AI_API_KEY 等配置项
    """
    """Configure the AI provider from application settings."""
    ai_config = AIProviderConfig(
        provider=settings.AI_PROVIDER,            # AI 提供商（如 deepseek）
        api_key=settings.AI_API_KEY,              # API 密钥
        model=settings.AI_MODEL,                  # 模型名称
        temperature=settings.AI_TEMPERATURE,      # 生成温度
        base_url=settings.AI_BASE_URL,            # 远程 API 基础 URL
        local_base_url=settings.AI_LOCAL_BASE_URL,  # 本地模型基础 URL
        is_local_first=settings.AI_LOCAL_FIRST,   # 是否优先使用本地模型
    )
    ai_service.configure(ai_config)


def create_lifespan(settings: Settings):
    """创建 FastAPI 生命周期处理器（工厂函数）。

    本函数是一个高阶函数：它接收 Settings 配置，返回一个异步上下文管理器。
    FastAPI 会在应用启动时进入这个上下文管理器（yield 之前的部分），
    在应用关闭时退出（yield 之后的部分）。

    为什么用工厂函数而不是直接定义 lifespan：
        因为需要在启动时注入配置（settings），通过闭包捕获的方式
        将配置传递给内部的 lifespan 函数。

    Args:
        settings: 应用全局配置实例

    Returns:
        一个异步上下文管理器，可直接传给 FastAPI 的 ``lifespan`` 参数
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # ===== 启动阶段（yield 之前）=====
        # 1. 配置日志系统
        configure_logging()
        # 2. 初始化数据库（创建表、标记 Alembic 版本）
        await init_db()
        # 3. 使用独立会话执行种子数据填充（确保系统有默认训练舱数据）
        async with AsyncSessionLocal() as db:
            await seed_deck(db)
        # 4. 初始化 AI 服务（配置大模型提供商连接）
        configure_ai_service(settings)
        try:
            # ===== 运行阶段 =====
            # yield 把控制权交给 FastAPI，应用开始接收请求
            # 当应用关闭时，代码从 yield 后面继续执行
            yield
        finally:
            # ===== 关闭阶段 =====
            # 关闭 AI 服务的 HTTP 客户端等资源，防止资源泄露
            await ai_service.aclose()

    return lifespan
