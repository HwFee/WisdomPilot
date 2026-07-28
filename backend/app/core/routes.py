"""HTTP route registration.

Registers auth and training domain routers plus lightweight health endpoints.
"""

from fastapi import FastAPI

from app.config import Settings
from app.auth import auth_router
from app.training.router import router as training_router

CORE_ROUTERS = (
    auth_router,
    training_router,
)


def include_routers(app: FastAPI, settings: Settings) -> None:
    """Register API routers."""
    for router in CORE_ROUTERS:
        app.include_router(router)


def register_health_routes(app: FastAPI) -> None:
    """Register lightweight health endpoints."""

    @app.get("/")
    async def root():
        return {"status": "ok", "message": "智码领航 API is running"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}
