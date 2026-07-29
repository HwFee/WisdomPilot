# =====================================================================
# 认证依赖注入模块
# ---------------------------------------------------------------------
# 本文件定义 FastAPI 依赖注入函数，用于从 HTTP 请求中提取并验证当前用户。
#
# FastAPI 依赖注入（Depends）工作原理：
#   - 路由函数声明参数 `current_user: User = Depends(get_current_user)`
#   - 请求到达时，FastAPI 自动调用 get_current_user，将其返回值注入路由函数
#   - 依赖链可嵌套：get_current_active_user 依赖 get_current_user
#
# 认证流程：
#   1. HTTPBearer 自动从 Authorization 头提取 Bearer token
#   2. decode_token 验证 JWT 签名和过期时间
#   3. 从载荷中提取 user_id，查询数据库获取 User 对象
#   4. 检查用户是否存在且账户激活
# =====================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db  # 数据库会话依赖
from app.auth.models import User
from app.auth.security import decode_token  # JWT 解码函数

# 以下常量定义认证失败时的 HTTP 响应详情消息
INVALID_CREDENTIALS_DETAIL = "Could not validate credentials"
INACTIVE_ACCOUNT_DETAIL = "User account is inactive"

# HTTPBearer 是 FastAPI 内置的安全依赖：
# - 自动从请求头 Authorization: Bearer <token> 中提取 token
# - 如果请求未携带 token，自动返回 403（可配置为 401）
# - 返回 HTTPAuthorizationCredentials 对象，.credentials 属性即 token 字符串
security = HTTPBearer()


async def _find_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    """从 Bearer 凭据中提取并查找用户。

    这是内部辅助函数，封装了"解码 JWT → 提取 user_id → 查询数据库"的完整链路。
    任何一步失败都返回 None，由调用方决定如何响应。

    Args:
        credentials: HTTPBearer 提取的凭据对象，None 表示请求未携带 token。
        db: 异步数据库会话。

    Returns:
        查找到的 User 对象，任何验证步骤失败则返回 None。
    """
    if credentials is None:
        # 请求未携带 Authorization 头
        return None

    # 解码并验证 JWT（检查签名 + 过期时间）
    payload = decode_token(credentials.credentials)
    if payload is None:
        # JWT 无效（签名错误、已过期、格式错误等）
        return None

    # JWT 载荷中 "sub"（subject）字段存储用户 ID
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        # 载荷格式异常，user_id 不是字符串
        return None

    # 按 user_id 查询数据库
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def _invalid_credentials_exception() -> HTTPException:
    """构造"凭据无效"的 HTTP 异常。

    Returns:
        401 Unauthorized 异常，响应头包含 WWW-Authenticate: Bearer，
        提示客户端需要 Bearer 认证。
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_CREDENTIALS_DETAIL,
        # WWW-Authenticate 头告知客户端认证方案，符合 HTTP 401 规范
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI 依赖：获取当前认证用户。

    这是最核心的认证依赖，被所有需要登录的路由使用。
    完整流程：提取 token → 解码 JWT → 查询用户 → 检查激活状态。

    Args:
        credentials: HTTPBearer 自动注入的凭据对象。
        db: get_db 自动注入的异步数据库会话。

    Returns:
        当前认证的 User 对象。

    Raises:
        HTTPException(401): token 无效或用户不存在。
        HTTPException(403): 用户账户已被停用。
    """
    # 从凭据中查找用户（解码 JWT + 查询数据库）
    user = await _find_user_from_credentials(credentials, db)
    if user is None:
        # token 无效或用户不存在，返回 401
        raise _invalid_credentials_exception()
    if not user.is_active:
        # 用户存在但账户停用，返回 403（认证通过但无权访问）
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INACTIVE_ACCOUNT_DETAIL,
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI 依赖：确保当前用户是激活用户。

    此依赖在 get_current_user 基础上额外保证用户已激活。
    目前 get_current_user 内部已检查 is_active，此函数作为语义层保留，
    便于未来扩展更细粒度的访问控制（如邮箱验证、付费状态等）。

    Args:
        current_user: 由 get_current_user 注入的当前用户。

    Returns:
        当前激活的 User 对象。
    """
    return current_user
