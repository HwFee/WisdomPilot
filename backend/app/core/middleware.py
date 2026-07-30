"""
中间件模块：限流 + CORS 跨域配置。

本模块为 FastAPI 应用注册两类中间件：

1. **限流中间件（RateLimitMiddleware）**：
   - 使用滑动窗口算法实现内存级限流
   - 对 ``/api/auth/*`` 端点按 IP 进行限流，防止暴力破解密码
   - 健康检查、文档等路径豁免限流

2. **CORS 跨域中间件（CORSMiddleware）**：
   - 生产环境通过 ``CORS_ORIGINS`` 配置项（环境变量 / .env）精确白名单放行
   - 开发期（DEBUG=True）额外用正则放行本地回环与私有网段（localhost / 127.0.0.1 / 10.x / 172.16-31.x / 192.168.x）

中间件执行顺序（Starlette 规则）：
    后注册的先执行。本模块先注册 RateLimitMiddleware，再注册 CORSMiddleware，
    因此实际请求处理顺序是：CORS -> RateLimit -> 路由处理 -> 响应返回。
"""

import time
import logging
from typing import Optional

from anyio.functools import lru_cache
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
        time.monotonic(): 绝对值无意义，但永远是单调递增，可以用来算差值，起点平台定义，可能是开机时间,不受系统改时影响
        time.time():从Unix纪元开始，不保证单增，受系统改时影响

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
        self._entries: dict[str, list[float]] = {}# {ip : [time1,time2,...]}

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
        #如果是空列表也能正常返回[] 相比于 _entries[key]  会抛出异常
        timestamps = self._entries.get(key, [])# python 中的默认赋值是引用，但不完全等于c++中的引用，而是类似于指针

        # 清除过期的时间戳：只保留窗口内的记录
        # Purge expired entries
        cutoff = now - self.window_seconds
        #直接改变timestamps的指向 让它指向过滤后的列表
        #如果要原地改可能需要timestamps[:] 切片赋值  但这里为了兼容默认返回的空列表空列表[] 采用显式赋值
        timestamps = [t for t in timestamps if t > cutoff]

        self._entries[key] = timestamps


        # 如果窗口内的请求数已达上限，拒绝
        if len(timestamps) >= self.max_requests:
            return False

        # 记录本次请求的时间戳
        #引用赋值
        timestamps.append(now)
        return True

    def reset(self) -> None:
        """清空所有限流记录，使限流器回到初始状态（主要用于测试重置）。

        将每个 key 的时间戳记录全部移除。封装在类内部，避免外部直接
        访问 ``_entries`` 这个实现细节。
        """
        self._entries.clear()


@lru_cache()
def _get_auth_limiter() -> RateLimiter:
    """获取认证限流器实例（@lru_cache 单例）。

    第一次调用时根据配置创建 RateLimiter 实例，后续调用直接返回缓存实例。
    使用 @lru_cache 延迟到首次调用时才读配置，避免在模块导入时调用
    get_settings()（此时 .env 可能尚未加载）。

    Returns:
        RateLimiter: 全局唯一的认证限流器实例
    """
    settings = get_settings()
    return RateLimiter(
        max_requests=settings.AUTH_RATE_WINDOW_MAX_REQUESTS,  # 窗口内最大请求数
        window_seconds=settings.AUTH_RATE_WINDOW_SECONDS,    # 窗口大小（秒）
    )


def reset_rate_limiters() -> None:
    """清空限流器状态（主要用于测试）。

    在测试场景中，需要在测试之间重置限流状态，确保每个测试用例
    从干净的状态开始。
    """
    """Clear limiter state, initializing lazy global when needed."""
    _get_auth_limiter().reset()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件 - 对认证端点进行速率限制。

    继承自 Starlette 的 ``BaseHTTPMiddleware``，在请求到达路由之前
    检查请求频率。当前只对 ``/api/auth/*`` 路径按 IP 进行限流，
    防止暴力破解登录接口。

    ``/api/auth/*`` endpoints use the auth rate limiter (per IP).
    """

    async def dispatch(self, request: Request, call_next):
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
        # request.client 是 @property，类型检查器对 property 的 None-narrowing 不生效，
        # 必须先取到局部变量，才能在 if 块内安全访问 .host
        if client := request.client:
            return client.host
        return "unknown"


# ---------------------------------------------------------------------------
# CORS - 跨域资源共享配置
# ---------------------------------------------------------------------------

# 开发期放行的本地来源正则：仅匹配回环地址与私有网段（带可选端口），不含公网 IP。
# 生产环境（DEBUG=False）不启用此正则，只认 allow_origins 精确白名单。
ALLOW_LOCAL_ORIGIN_REGEX = (
    r"https?://localhost(?::\d+)?"                                      # localhost:任意端口
    r"|https?://127\.0\.0\.1(?::\d+)?"                                  # 回环地址
    r"|https?://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?"                 # 10.0.0.0/8 私有网段
    r"|https?://172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}(?::\d+)?"   # 172.16.0.0/12 私有网段
    r"|https?://192\.168\.\d{1,3}\.\d{1,3}(?::\d+)?"                    # 192.168.0.0/16 私有网段
)


def get_cors_origins() -> list[str]:
    """获取 CORS 允许的来源列表（精确白名单）。

    只返回 ``Settings.CORS_ORIGINS`` 配置的生产环境来源（逗号分隔）；
    本地开发地址不走此列表，由 ``ALLOW_LOCAL_ORIGIN_REGEX`` 在开发期放行。

    ``CORS_ORIGINS`` 由 Pydantic Settings 统一从环境变量 / .env 读取，
    例如 ``CORS_ORIGINS=https://app.example.com,https://www.example.com``。

    Returns:
        list[str]: 生产环境允许的 CORS 来源 URL 列表
    """
    cors_origins: list[str] = []
    production_origins = get_settings().CORS_ORIGINS

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
    settings = get_settings()
    # 先注册限流中间件（会在 CORS 之后执行）
    # noinspection PyTypeChecker,PyArgumentList
    # PyCharm 推断不出中间件 __init__ 签名，误报类型不匹配 / 意外实参，属上游签名问题
    app.add_middleware(RateLimitMiddleware)
    # 再注册 CORS 中间件（最先执行，处理跨域预检请求）
    # 正则仅开发期（DEBUG=True）启用，放行本地回环/私有网段；生产只认 allow_origins 白名单
    # noinspection PyTypeChecker,PyArgumentList
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),       # 生产环境精确白名单
        allow_origin_regex=ALLOW_LOCAL_ORIGIN_REGEX if settings.DEBUG else None,# 开发期间正则表达
        allow_credentials=True,                 # 允许携带 Cookie
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # 允许的 HTTP 方法
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # 允许的请求头
    )
