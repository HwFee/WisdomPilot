EMAIL_ALREADY_REGISTERED_MESSAGE = "该邮箱已被注册"
USERNAME_ALREADY_REGISTERED_MESSAGE = "该用户名已被使用"
INVALID_CREDENTIALS_MESSAGE = "用户名或密码错误"
INACTIVE_ACCOUNT_MESSAGE = "Account is inactive"


class AuthError(Exception):
    """Base class for expected authentication use-case failures."""


class EmailAlreadyRegisteredError(AuthError):
    def __init__(self) -> None:
        super().__init__(EMAIL_ALREADY_REGISTERED_MESSAGE)


class UsernameAlreadyRegisteredError(AuthError):
    def __init__(self) -> None:
        super().__init__(USERNAME_ALREADY_REGISTERED_MESSAGE)


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS_MESSAGE)


class InactiveAccountError(AuthError):
    def __init__(self) -> None:
        super().__init__(INACTIVE_ACCOUNT_MESSAGE)
