"""FastAPI application entry point."""

from fastapi import FastAPI

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import create_lifespan
from app.core.middleware import configure_middleware
from app.core.routes import include_routers, register_health_routes

APP_TITLE = "智码领航 API"
APP_DESCRIPTION = "AI-powered Programming Teaching Platform API"
APP_VERSION = "1.0.0"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=create_lifespan(settings),
    )

    configure_middleware(app)
    include_routers(app, settings)
    register_health_routes(app)
    register_exception_handlers(app)

    return app


app = create_app()
