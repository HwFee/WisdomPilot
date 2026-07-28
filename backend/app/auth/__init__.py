"""Auth domain — user model, schemas, service, router, and security.

All auth-related code lives here. Import from this package or directly from
submodules as needed.
"""

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
    UsernameAlreadyRegisteredError,
)
from app.auth.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.router import router as auth_router

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
    "UsernameAlreadyRegisteredError",
    "auth_router",
    "create_access_token",
    "decode_token",
    "get_current_active_user",
    "get_current_user",
    "get_password_hash",
    "verify_password",
]
