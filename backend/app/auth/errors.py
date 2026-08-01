# =====================================================================
# 认证错误类型定义模块
# ---------------------------------------------------------------------
# 本文件定义认证域所有"预期的业务异常"。
#
# 为什么用自定义异常而不是直接抛 HTTPException？
#   - 分层架构原则：service 层只关心业务逻辑，不应知道 HTTP 状态码；
#     service 抛出领域异常（如 InvalidCredentialsError），由 router 层
#     捕获后转换为对应的 HTTP 响应。这样 service 可被复用（如 CLI、测试）。
#   - 所有异常继承 AuthError，调用方可用 except AuthError 统一捕获。
# =====================================================================

# 以下常量定义各异常对应的用户可见错误消息（中文），集中管理便于国际化维护。
EMAIL_ALREADY_REGISTERED_MESSAGE = "该邮箱已被注册"
USERNAME_ALREADY_REGISTERED_MESSAGE = "该用户名已被使用"
INVALID_CREDENTIALS_MESSAGE = "用户名或密码错误"
# 账户停用提示（当前保留英文，因前端可能依赖该字符串做匹配）
INACTIVE_ACCOUNT_MESSAGE = "Account is inactive"


class AuthError(Exception):
    """认证域预期业务失败的基类。

    认证域所有预期异常的基类。

    设计意图：所有认证相关的业务错误都继承此基类，调用方可以用
    `except AuthError` 统一捕获，无需逐个列出子类。
    """


class EmailAlreadyRegisteredError(AuthError):
    """注册时邮箱已存在异常。"""

    def __init__(self) -> None:
        super().__init__(EMAIL_ALREADY_REGISTERED_MESSAGE)


class UsernameAlreadyRegisteredError(AuthError):
    """注册时用户名已存在异常。"""

    def __init__(self) -> None:
        super().__init__(USERNAME_ALREADY_REGISTERED_MESSAGE)


class InvalidCredentialsError(AuthError):
    """登录凭据无效异常（用户名不存在或密码不匹配）。

    安全说明：不区分"用户不存在"和"密码错误"，统一返回相同消息，
    防止攻击者通过响应差异枚举有效用户名。
    """

    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS_MESSAGE)


class InactiveAccountError(AuthError):
    """账户已被停用异常。用户存在且密码正确，但 is_active=False。"""

    def __init__(self) -> None:
        super().__init__(INACTIVE_ACCOUNT_MESSAGE)
