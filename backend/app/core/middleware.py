"""
中间件模块：限流 + CORS 跨域配置。

本模块为 FastAPI 应用注册两类中间件：

1. **限流中间件（RateLimitMiddleware）**：
   - 使用滑动窗口算法实现内存级限流
   - 对 ``/api/auth/*`` 端点按 IP 进行限流，防止暴力破解密码
   - 健康检查、文档等路径豁免限流

2. **CORS 跨域中间件（CORSMiddleware）**：
   - 允许前端（如 localhost:3000）跨域访问后端 API
   - 支持通过环境变量 ``CORS_ORIGINS`` 配置生产环境的允许域名
   - 同时支持正则匹配本地开发地址（localhost / 127.0.0.1 / IP 地址）

中间件执行顺序（Starlette 规则）：
    后注册的先执行。本模块先注册 RateLimitMiddleware，再注册 CORSMiddleware，
    因此实际请求处理顺序是：CORS -> RateLimit -> 路由处理 -> 响应返回。
"""

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
# Rate limiting - 限流部分
# ---------------------------------------------------------------------------

# 豁免限流的路径集合：这些路径是公开的、无副作用的，不需要限流
# Exempted paths that do not need rate limiting
EXEMPT_PATHS = {
    "/",             # 根路径健康检查
    "/health",       # 健康检查端点
    "/docs",         # Swagger UI 文档页面
    "/openapi.json",  # OpenAPI 规范 JSON
    "/redoc",        # ReDoc 文档页面
}


class RateLimiter:
    """滑动窗口限流器（基于内存字典）。

    使用滑动窗口算法：记录每个 key（如 IP 地址）的请求时间戳列表，
    每次请求时清除窗口外的过期时间戳，如果窗口内的时间戳数量超过限制则拒绝请求。

    设计特点：
        - 纯内存实现，不依赖 Redis 等外部服务（适合单实例部署）
        - 使用 ``time.monotonic()`` 而非 ``time.time()``，不受系统时间调整影响
        - 惰性清理：只在每次请求时清理过期时间戳，没有后台定时任务

    属性:
        max_requests: 窗口内允许的最大请求数
        window_seconds: 时间窗口大小（秒），默认 60 秒
        _entries: 存储 key -> [时间戳列表] 的字典

    Tracks timestamps per key (e.g. IP or user_id), purges entries
    older than the window, and denies requests that exceed the limit.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        """初始化限流器。

        Args:
            max_requests: 在时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒），默认 60 秒
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # 使用字典存储每个 key 的请求时间戳列表
        self._entries: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """检查指定 key 的请求是否被允许。

        算法步骤：
            1. 获取当前单调时间
            2. 清除窗口外的过期时间戳（滑动窗口的核心）
            3. 如果剩余时间戳数 >= 最大请求数，拒绝请求
            4. 否则记录当前时间戳，允许请求

        Args:
            key: 限流标识，通常是 ``ip:192.168.1.1`` 这样的格式

        Returns:
            bool: True 表示请求被允许，False 表示被限流
        """
        # 使用 monotonic() 而非 time.time()，因为 monotonic 不受系统时间回拨影响
        now = time.monotonic()
        timestamps = self._entries.get(key, [])

        # 清除过期的时间戳：只保留窗口内的记录
        # Purge expired entries
        cutoff = now - self.window_seconds
        timestamps = [t for t in timestamps if t > cutoff]
        self._entries[key] = timestamps

        # 如果窗口内的请求数已达上限，拒绝
        if len(timestamps) >= self.max_requests:
            return False

        # 记录本次请求的时间戳
        timestamps.append(now)
        return True


# 惰性初始化的全局限流器实例
# 避免在模块导入时调用 get_settings()（此时 .env 可能尚未加载）
# Lazily-initialized global limiter to avoid calling get_settings() at import time.
_auth_limiter: Optional[RateLimiter] = None


def _get_auth_limiter() -> RateLimiter:
    """获取认证限流器实例（惰性初始化单例）。

    第一次调用时根据配置创建 RateLimiter 实例，后续调用直接返回缓存的实例。
    使用惰性初始化是为了避免在模块导入时就读取配置（此时 .env 可能还没加载好）。

    Returns:
        RateLimiter: 全局唯一的认证限流器实例
    """
    global _auth_limiter
    if _auth_limiter is None:
        _auth_limiter = RateLimiter(
            max_requests=get_settings().AUTH_RATE_PER_MINUTE,  # 每分钟最大请求数
            window_seconds=60,                                  # 60 秒窗口
        )
    return _auth_limiter


def reset_rate_limiters() -> None:
    """清空限流器状态（主要用于测试）。

    在测试场景中，需要在测试之间重置限流状态，确保每个测试用例
    从干净的状态开始。
    """
    """Clear limiter state, initializing lazy global when needed."""
    _get_auth_limiter()._entries.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件 - 对认证端点进行速率限制。

    继承自 Starlette 的 ``BaseHTTPMiddleware``，在请求到达路由之前
    检查请求频率。当前只对 ``/api/auth/*`` 路径按 IP 进行限流，
    防止暴力破解登录接口。

    ``/api/auth/*`` endpoints use the auth rate limiter (per IP).
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """中间件请求处理逻辑。

        处理流程：
            1. 获取请求路径
            2. 豁免路径直接放行
            3. 如果是认证端点（``/api/auth/``），使用认证限流器按 IP 限流
            4. 超出限流则返回 429 状态码
            5. 未超出则继续传递给下一个中间件或路由

        Args:
            request: Starlette 请求对象
            call_next: 下一个中间件/路由的调用函数

        Returns:
            Response: 正常请求返回路由响应，限流请求返回 429 JSON 响应
        """
        path = request.url.path

        # 豁免路径不做限流（健康检查、API 文档等）
        # Skip exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)

        limiter: Optional[RateLimiter] = None
        rate_key: Optional[str] = None

        # 对认证端点按 IP 限流
        if path.startswith("/api/auth/"):
            limiter = _get_auth_limiter()
            # 限流 key 格式：ip:客户端IP地址
            rate_key = f"ip:{self._get_client_ip(request)}"

        # 如果配置了限流器且请求被拒绝，返回 429
        if limiter and rate_key and not limiter.is_allowed(rate_key):
            logger.warning("Rate limit exceeded for key=%s path=%s", rate_key, path)
            return JSONResponse(
                status_code=429,  # 429 Too Many Requests
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        # 请求通过限流检查，传递给下一个处理器
        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """从请求中提取客户端 IP 地址。

        Args:
            request: Starlette 请求对象

        Returns:
            str: 客户端 IP 地址，如果无法获取则返回 "unknown"
        """
        if request.client:
            return request.client.host
        return "unknown"


# ---------------------------------------------------------------------------
# CORS - 跨域资源共享配置
# ---------------------------------------------------------------------------

# 默认允许的 CORS 来源：本地开发服务器地址
DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:3000",   # Next.js 开发服务器
    "http://127.0.0.1:3000",   # Next.js 开发服务器（IP 访问）
)
# 允许的来源正则：匹配 localhost / 127.0.0.1 / 任意 IP 地址（带可选端口）
# 这样开发者在不同端口运行前端时也能正常跨域访问
ALLOW_LOCAL_ORIGIN_REGEX = (
    r"https?://localhost(:\d+)?|"           # localhost:任意端口
    r"https?://127\.0\.0\.1(:\d+)?|"        # 127.0.0.1:任意端口
    r"https?://\d+\.\d+\.\d+\.\d+(:\d+)?"   # 任意IP:任意端口
)
# 环境变量名：通过该变量配置生产环境的 CORS 来源（逗号分隔）
CORS_ORIGINS_ENV = "CORS_ORIGINS"


def get_cors_origins() -> list[str]:
    """获取 CORS 允许的来源列表。

    合并默认来源和环境变量配置的来源：
        1. 始终包含默认的本地开发地址
        2. 如果设置了 ``CORS_ORIGINS`` 环境变量，解析并追加生产域名

    环境变量格式（逗号分隔）：
        ``CORS_ORIGINS=https://app.example.com,https://www.example.com``

    Returns:
        list[str]: 所有允许的 CORS 来源 URL 列表
    """
    """Return default and environment-provided CORS origins."""
    cors_origins = list(DEFAULT_CORS_ORIGINS)
    # 从环境变量读取生产环境的 CORS 来源
    production_origins = os.environ.get(CORS_ORIGINS_ENV, "")

    if production_origins:
        # 按逗号分割，去除空白后追加到来源列表
        cors_origins.extend(
            origin.strip() for origin in production_origins.split(",") if origin.strip()
        )

    return cors_origins


def configure_middleware(app: FastAPI) -> None:
    """注册所有中间件到 FastAPI 应用。

    注册顺序说明（Starlette 中间件按注册的逆序执行）：
        1. 先注册 RateLimitMiddleware -> 最后执行（在 CORS 之后）
        2. 再注册 CORSMiddleware -> 最先执行（每个请求第一个经过的中间件）

    实际请求处理链：
        请求 -> CORS -> RateLimit -> 路由处理 -> RateLimit响应 -> CORS响应 -> 客户端

    Args:
        app: FastAPI 应用实例
    """
    """Register middleware in the order required by Starlette."""
    # 先注册限流中间件（会在 CORS 之后执行）
    app.add_middleware(RateLimitMiddleware)
    # 再注册 CORS 中间件（最先执行，处理跨域预检请求）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),       # 允许的来源列表
        allow_origin_regex=ALLOW_LOCAL_ORIGIN_REGEX,  # 允许的来源正则
        allow_credentials=True,                 # 允许携带 Cookie
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # 允许的 HTTP 方法
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # 允许的请求头
    )
