"""
HTTP 路由注册模块。

本模块负责将所有 API 路由器统一注册到 FastAPI 应用实例上，
并提供轻量级的健康检查端点。

当前注册的路由组：
    - ``auth_router``: 认证路由（登录、注册、刷新令牌等），前缀 ``/api/auth``
    - ``training_router``: 训练舱域路由（题目、掌握度、徽章等），前缀 ``/api``

健康检查端点：
    - ``GET /``:       根路径，返回服务状态
    - ``GET /health``: 健康检查，用于负载均衡器/K8s 探针

Registers auth and training domain routers plus lightweight health endpoints.
"""

from fastapi import FastAPI

from app.config import Settings
# 导入认证路由器（包含登录、注册等端点）
from app.auth import auth_router
# 导入训练舱域路由器（包含题目、掌握度、徽章等端点）
from app.training.router import router as training_router

# 所有需要在应用上注册的路由器元组
# 注册顺序决定了 Swagger 文档中端点的排列顺序
CORE_ROUTERS = (
    auth_router,       # /api/auth/* - 认证相关
    training_router,   # /api/*      - 训练舱域
)


def include_routers(app: FastAPI, _settings: Settings) -> None:
    """注册所有 API 路由器到 FastAPI 应用。

    遍历 ``CORE_ROUTERS`` 元组中的所有路由器，逐个注册到应用实例上。
    每个路由器内部已经定义了各自的前缀（如 ``/api/auth``、``/api``）和标签。

    Args:
        app: FastAPI 应用实例
        _settings: 应用配置（当前未直接使用，但保留以备将来按配置动态注册路由）
    """
    """Register API routers."""
    for router in CORE_ROUTERS:
        app.include_router(router)


def register_health_routes(app: FastAPI) -> None:
    """注册轻量级健康检查端点。

    添加两个简单的 GET 端点用于服务健康检查：
        - ``GET /``: 根路径检查，返回服务运行状态
        - ``GET /health``: 标准健康检查端点，常用于 K8s liveness/readiness 探针

    这些端点不经过限流和认证，是公开可访问的。

    Args:
        app: FastAPI 应用实例
    """
    """Register lightweight health endpoints."""

    @app.get("/")
    async def root():
        """根路径端点 - 返回服务运行状态。

        用于快速验证服务是否正常启动。返回中文字符串表明中文支持正常。
        """
        return {"status": "ok", "message": "WisdomPilot API is running"}

    @app.get("/health")
    async def health():
        """健康检查端点 - 返回简单的健康状态。

        常用于负载均衡器或 K8s 的健康探针，返回 200 表示服务健康。
        """
        return {"status": "healthy"}
