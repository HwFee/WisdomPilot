"""Application startup and shutdown lifecycle."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app import models as _register_auth_models  # noqa: F401 - 注册 User 进 Base.metadata
from app.deck import models as _register_deck_models  # noqa: F401 - register deck models before init_db
from app.config import Settings

# 显式引用副作用 import：二者仅为在建表前把模型注册进 Base.metadata
_MODELS_REGISTERED = (_register_auth_models, _register_deck_models)
from app.database import AsyncSessionLocal, init_db
from app.deck.seed import seed_deck
from app.schemas.ai import AIProviderConfig
from app.services.ai import ai_service

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
APP_SERVICES_LOGGER = "app.services"


def configure_logging() -> None:
    """Configure application logging once during startup."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logging.getLogger(APP_SERVICES_LOGGER).setLevel(logging.INFO)


def configure_ai_service(settings: Settings) -> None:
    """Configure the AI provider from application settings."""
    ai_config = AIProviderConfig(
        provider=settings.AI_PROVIDER,
        api_key=settings.AI_API_KEY,
        model=settings.AI_MODEL,
        temperature=settings.AI_TEMPERATURE,
        base_url=settings.AI_BASE_URL,
        local_base_url=settings.AI_LOCAL_BASE_URL,
        is_local_first=settings.AI_LOCAL_FIRST,
    )
    ai_service.configure(ai_config)


def create_lifespan(settings: Settings):
    """Create the FastAPI lifespan handler with injected settings."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        await init_db()
        async with AsyncSessionLocal() as db:
            await seed_deck(db)
        configure_ai_service(settings)
        try:
            yield
        finally:
            await ai_service.aclose()

    return lifespan
