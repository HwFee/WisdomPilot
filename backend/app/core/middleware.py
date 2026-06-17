"""Middleware registration for the FastAPI application."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import RateLimitMiddleware

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
ALLOW_LOCAL_ORIGIN_REGEX = (
    r"https?://localhost(:\d+)?|"
    r"https?://127\.0\.0\.1(:\d+)?|"
    r"https?://\d+\.\d+\.\d+\.\d+(:\d+)?"
)
CORS_ORIGINS_ENV = "CORS_ORIGINS"


def get_cors_origins() -> list[str]:
    """Return default and environment-provided CORS origins."""
    cors_origins = list(DEFAULT_CORS_ORIGINS)
    production_origins = os.environ.get(CORS_ORIGINS_ENV, "")

    if production_origins:
        cors_origins.extend(
            origin.strip()
            for origin in production_origins.split(",")
            if origin.strip()
        )

    return cors_origins


def configure_middleware(app: FastAPI) -> None:
    """Register middleware in the order required by Starlette."""
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_origin_regex=ALLOW_LOCAL_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )
