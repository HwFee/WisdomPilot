"""Middleware: rate limiting + CORS registration for the FastAPI application."""

import os
import time
import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

# Exempted paths that do not need rate limiting
EXEMPT_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class RateLimiter:
    """Sliding window rate limiter using in-memory dict.

    Tracks timestamps per key (e.g. IP or user_id), purges entries
    older than the window, and denies requests that exceed the limit.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._entries: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        timestamps = self._entries.get(key, [])

        # Purge expired entries
        cutoff = now - self.window_seconds
        timestamps = [t for t in timestamps if t > cutoff]
        self._entries[key] = timestamps

        if len(timestamps) >= self.max_requests:
            return False

        timestamps.append(now)
        return True


# Lazily-initialized global limiter to avoid calling get_settings() at import time.
_auth_limiter: Optional[RateLimiter] = None


def _get_auth_limiter() -> RateLimiter:
    global _auth_limiter
    if _auth_limiter is None:
        _auth_limiter = RateLimiter(
            max_requests=get_settings().AUTH_RATE_PER_MINUTE,
            window_seconds=60,
        )
    return _auth_limiter


def reset_rate_limiters() -> None:
    """Clear limiter state, initializing lazy global when needed."""
    _get_auth_limiter()._entries.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that applies rate limiting to auth endpoints.

    ``/api/auth/*`` endpoints use the auth rate limiter (per IP).
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        path = request.url.path

        # Skip exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)

        limiter: Optional[RateLimiter] = None
        rate_key: Optional[str] = None

        if path.startswith("/api/auth/"):
            limiter = _get_auth_limiter()
            rate_key = f"ip:{self._get_client_ip(request)}"

        if limiter and rate_key and not limiter.is_allowed(rate_key):
            logger.warning("Rate limit exceeded for key=%s path=%s", rate_key, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        if request.client:
            return request.client.host
        return "unknown"


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
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
            origin.strip() for origin in production_origins.split(",") if origin.strip()
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
