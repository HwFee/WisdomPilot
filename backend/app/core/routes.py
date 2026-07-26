"""HTTP route registration.

训练舱重构后只保留认证与训练舱 API；旧模块（课程/AI/经济/社区）已废弃，
对应的 router 文件保留在 app/routers/ 但不再注册。
"""

from fastapi import FastAPI

from app.config import Settings
from app.deck.router import router as deck_router
from app.routers import auth_router

CORE_ROUTERS = (
    auth_router,
    deck_router,
)


def include_routers(app: FastAPI, settings: Settings) -> None:
    """Register API routers."""
    for router in CORE_ROUTERS:
        app.include_router(router)


def register_websocket_routes(app: FastAPI) -> None:
    """训练舱不使用 WebSocket，保留空实现以兼容 app 装配。"""


def register_health_routes(app: FastAPI) -> None:
    """Register lightweight health endpoints."""

    @app.get("/")
    async def root():
        return {"status": "ok", "message": "智码领航 API is running"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}
