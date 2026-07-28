from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.models import User
from app.auth.schemas import UserCreate, UserLogin, Token, UserResponse, ForgotPasswordRequest
from app.auth.service import AuthService
from app.auth.errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
FORGOT_PASSWORD_RESPONSE_MESSAGE = (
    "If an account exists with that email, a password reset link has been sent."
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Register a new user"""
    service = AuthService(db)
    try:
        _, token = await service.register(user_data)
        return token
    except (EmailAlreadyRegisteredError, UsernameAlreadyRegisteredError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login with email and password"""
    service = AuthService(db)
    try:
        _, token = await service.login(login_data)
        return token
    except (InvalidCredentialsError, InactiveAccountError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Send password reset email.

    Always returns 200 regardless of whether the email exists,
    to prevent user enumeration attacks (C6).
    """
    service = AuthService(db)
    await service.forgot_password(request.email)
    return {"message": FORGOT_PASSWORD_RESPONSE_MESSAGE}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current authenticated user info"""
    return UserResponse.model_validate(current_user)
