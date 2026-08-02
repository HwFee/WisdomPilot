"""认证域包：用户模型、Schema、服务层、路由与安全工具。

所有认证相关代码都集中在本包中。可按需从本包导入，
也可以直接从各子模块导入。
"""

# =====================================================================
# 认证域包（auth package）初始化文件
# ---------------------------------------------------------------------
# 本文件是 backend/app/auth/ 目录的包入口，职责是将认证域内的核心组件
# （数据模型、Pydantic schema、服务层、安全工具、依赖注入、错误类型、
# 路由器）统一导出，使外部模块只需 `from app.auth import xxx` 即可使用。
#
# 设计意图：
#   - 对外提供"门面"（facade），隐藏内部子模块结构，降低耦合
#   - __all__ 列表显式声明公开 API，防止内部符号意外泄露
#   - 训练舱重构后，认证域只负责用户注册/登录/JWT，不再包含旧系统字段
# =====================================================================

from app.auth.models import User
from app.auth.schemas import (
    ForgotPasswordRequest,
    Token,
    TokenData,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.auth.service import AuthService
from app.auth.errors import (
    AuthError,
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
)
from app.auth.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.router import router as auth_router

# __all__ 控制 `from app.auth import *` 时导出的符号集合，
# 也是对外公开 API 的显式声明清单。
__all__ = [
    "AuthError",
    "AuthService",
    "EmailAlreadyRegisteredError",
    "ForgotPasswordRequest",
    "InactiveAccountError",
    "InvalidCredentialsError",
    "Token",
    "TokenData",
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "auth_router",
    "create_access_token",
    "decode_token",
    "get_current_active_user",
    "get_current_user",
    "get_password_hash",
    "verify_password",
]
