"""Rate limiting middleware (C5, C8)"""

import time
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings
from app.utils.security import decode_token

logger = logging.getLogger(__name__)

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


# Lazily-initialized global limiters to avoid calling get_settings() at import time.
_auth_limiter: Optional[RateLimiter] = None
_code_limiter: Optional[RateLimiter] = None


def _get_auth_limiter() -> RateLimiter:
    global _auth_limiter
    if _auth_limiter is None:
        _auth_limiter = RateLimiter(
            max_requests=get_settings().AUTH_RATE_PER_MINUTE,
            window_seconds=60,
        )
    return _auth_limiter


def _get_code_limiter() -> RateLimiter:
    global _code_limiter
    if _code_limiter is None:
        _code_limiter = RateLimiter(
            max_requests=get_settings().CODE_EXEC_RATE_PER_MINUTE,
            window_seconds=60,
        )
    return _code_limiter


def reset_rate_limiters() -> None:
    """Clear limiter state, initializing lazy globals when needed."""
    _get_auth_limiter()._entries.clear()
    _get_code_limiter()._entries.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that applies rate limiting to specific endpoints.

    - ``/api/auth/*`` endpoints use the auth rate limiter (per IP).
    - ``/api/code/*`` endpoints use the code-exec rate limiter (per user_id
      extracted from the JWT token when available, otherwise per IP).
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
        elif path.startswith("/api/code/"):
            limiter = _get_code_limiter()
            rate_key = self._get_code_key(request)

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

    @staticmethod
    def _get_code_key(request: Request) -> str:
        """Return a per-user key from JWT, or fall back to IP."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"

        # Unauthenticated or invalid token -- use IP
        host = request.client.host if request.client else "unknown"
        return f"ip:{host}"
