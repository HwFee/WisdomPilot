# =====================================================================
# 认证路由模块
# ---------------------------------------------------------------------
# 本文件定义认证域所有 HTTP API 端点，挂载在 /api/auth 前缀下。
#
# 路由端点清单：
#   POST /api/auth/register        注册新用户
#   POST /api/auth/login           用户登录
#   POST /api/auth/forgot-password 忘记密码（安全占位）
#   GET  /api/auth/me              获取当前用户信息（需认证）
#
# 分层职责：
#   - router 只做 HTTP 层工作：接收请求、调用 service、异常转换、返回响应
#   - 业务逻辑全部委托给 AuthService
#   - 领域异常（AuthError 子类）在此转换为 HTTPException
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.models import User
from app.auth.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    ForgotPasswordRequest,
    ChangePasswordIn,
)
from app.auth.service import AuthService
from app.auth.security import get_password_hash, verify_password
from app.auth.errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
)
from app.auth.dependencies import get_current_active_user

# 创建路由器，所有端点统一挂载在 /api/auth 前缀下，标签 "auth" 用于 OpenAPI 文档分组
router = APIRouter(prefix="/api/auth", tags=["auth"])

# 忘记密码的统一响应消息：
# 无论邮箱是否存在都返回此消息，防止攻击者通过响应差异枚举已注册邮箱
FORGOT_PASSWORD_RESPONSE_MESSAGE = (
    "If an account exists with that email, a password reset link has been sent."
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """注册新用户（POST /api/auth/register）。

    注册新用户。

    成功返回 201 Created 和 JWT 令牌（含用户信息）。
    邮箱或用户名重复返回 400 Bad Request。

    Args:
        user_data: 注册请求体（email, username, password），Pydantic 自动验证。
        db: 异步数据库会话，由 Depends(get_db) 自动注入。

    Returns:
        Token 对象，包含 access_token 和 user 信息。
    """
    # 每次请求创建新的 AuthService 实例，注入当前请求的数据库会话
    service = AuthService(db)
    try:
        # service.register 返回 (User, Token) 元组，路由只需 Token
        _, token = await service.register(user_data)
        return token
    except EmailAlreadyRegisteredError as error:
        # 邮箱/用户名重复 → 400 Bad Request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """用户登录（POST /api/auth/login）。

    用户登录。

    成功返回 200 OK 和 JWT 令牌（含用户信息）。
    凭据错误或账户停用返回 401 Unauthorized。

    Args:
        login_data: 登录请求体（username/email, password, remember_me）。
        db: 异步数据库会话，由 Depends(get_db) 自动注入。

    Returns:
        Token 对象，包含 access_token 和 user 信息。
    """
    # 每次请求创建新的 AuthService 实例，注入当前请求的数据库会话
    service = AuthService(db)
    try:
        # service.login 返回 (User, Token) 元组，路由只需 Token
        _, token = await service.login(login_data)
        return token
    except (InvalidCredentialsError, InactiveAccountError) as error:
        # 凭据无效或账户停用 → 401 Unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """发送密码重置邮件。

    无论邮箱是否存在都返回 200，防止用户枚举攻击（C6）。

    忘记密码端点。

    安全设计：无论邮箱是否存在，始终返回 200 和相同的消息，
    防止攻击者通过响应差异判断邮箱是否已注册（用户枚举攻击防护）。

    Args:
        request: 忘记密码请求体（仅含 email 字段）。
        db: 异步数据库会话。

    Returns:
        包含统一提示消息的字典。
    """
    # 每次请求创建新的 AuthService 实例，注入当前请求的数据库会话
    service = AuthService(db)
    await service.forgot_password(request.email)
    # 始终返回相同的消息，不暴露邮箱是否存在
    return {"message": FORGOT_PASSWORD_RESPONSE_MESSAGE}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """获取当前登录用户信息（GET /api/auth/me）。

    获取当前登录用户信息。

    需要携带有效的 JWT 令牌（Authorization: Bearer <token>）。
    令牌无效或过期返回 401。

    Args:
        current_user: 由 get_current_active_user 依赖注入的当前用户对象。

    Returns:
        UserResponse 对象，包含用户的公开信息。
    """
    # 将 ORM 对象转换为响应 Schema
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """注销当前用户（POST /api/auth/logout）。

    将 token_version +1：该用户此前签发的所有 JWT 立即失效
    （dependencies 校验 token 载荷的 ver 与数据库不一致时拒绝）。

    Args:
        current_user: 当前登录用户。
        db: 异步数据库会话。

    Returns:
        确认消息。
    """
    current_user.token_version += 1
    await db.commit()
    return {"message": "Logged out"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    body: ChangePasswordIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """修改密码（POST /api/auth/change-password）。

    验证旧密码 → 重哈希新密码 → token_version +1 吊销所有旧 token。

    Args:
        body: 旧密码 + 新密码。
        current_user: 当前登录用户。
        db: 异步数据库会话。

    Returns:
        确认消息。
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="当前密码不正确")
    current_user.hashed_password = get_password_hash(body.new_password)
    current_user.token_version += 1
    await db.commit()
    return {"message": "Password changed"}
