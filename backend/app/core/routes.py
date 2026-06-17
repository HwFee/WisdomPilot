"""HTTP and WebSocket route registration."""

from fastapi import FastAPI, WebSocket
from starlette.datastructures import QueryParams

from app.config import Settings
from app.routers import (
    admin_router,
    auth_router,
    code_router,
    solutions_router,
    stats_router,
    users_router,
)
from app.routers.achievements import router as achievements_router
from app.routers.ai import (
    analysis_router,
    chat_router,
    choice_router,
    config_router,
    hint_router,
    review_router,
)
from app.routers.challenges import router as challenges_router
from app.routers.chapters import router as chapters_router
from app.routers.core import router as core_router
from app.routers.courses import router as courses_router
from app.routers.exercises import router as exercises_router
from app.routers.favorites import router as favorites_router
from app.routers.learning_path import router as learning_path_router
from app.routers.note_tags import router as note_tags_router
from app.routers.notes import router as notes_router
from app.routers.review import router as spaced_review_router
from app.routers.test_sandbox import router as test_sandbox_router
from app.routers.tier import router as tier_router
from app.routers.xp import router as xp_router
from app.websockets.exercise import exercise_websocket_endpoint

CORE_ROUTERS = (
    auth_router,
    users_router,
    admin_router,
    stats_router,
    code_router,
    courses_router,
)
AI_ROUTERS = (
    choice_router,
    review_router,
    config_router,
    chat_router,
    analysis_router,
    hint_router,
)
LEARNING_ROUTERS = (
    challenges_router,
    achievements_router,
    exercises_router,
    chapters_router,
    spaced_review_router,
    favorites_router,
    notes_router,
    note_tags_router,
    learning_path_router,
)
ECONOMY_ROUTERS = (
    tier_router,
    core_router,
    xp_router,
)
COMMUNITY_ROUTERS = (solutions_router,)


def include_routers(app: FastAPI, settings: Settings) -> None:
    """Register API routers in domain groups."""
    for router in CORE_ROUTERS:
        app.include_router(router)

    for router in AI_ROUTERS:
        app.include_router(router)

    for router in LEARNING_ROUTERS:
        app.include_router(router)

    for router in ECONOMY_ROUTERS:
        app.include_router(router)

    if settings.ENABLE_TEST_SANDBOX:
        app.include_router(test_sandbox_router)

    for router in COMMUNITY_ROUTERS:
        app.include_router(router)


def register_websocket_routes(app: FastAPI) -> None:
    """Register WebSocket endpoints."""

    @app.websocket("/ws/exercises")
    async def exercise_websocket(websocket: WebSocket):
        query_string = websocket.scope.get("query_string", b"").decode("utf-8")
        token = QueryParams(query_string).get("token", "")
        await exercise_websocket_endpoint(websocket, token)


def register_health_routes(app: FastAPI) -> None:
    """Register lightweight health endpoints."""

    @app.get("/")
    async def root():
        return {"status": "ok", "message": "智码领航 API is running"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}
