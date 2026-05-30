from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import UserCreate, UserLogin, Token, UserResponse, ForgotPasswordRequest
from app.services.auth import AuthService
from app.utils.deps import get_current_active_user
from app.models import User
import logging

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user"""
    service = AuthService(db)
    try:
        user, token = await service.register(user_data)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password"""
    service = AuthService(db)
    try:
        user, token = await service.login(login_data)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send password reset email.

    Always returns 200 regardless of whether the email exists,
    to prevent user enumeration attacks (C6).
    """
    service = AuthService(db)
    # Call the service silently -- it handles the lookup internally
    try:
        await service.forgot_password(request.email)
    except ValueError:
        # Even if the user doesn't exist, return the same 200 response
        pass

    return {"message": "If an account exists with that email, a password reset link has been sent."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user info"""
    return UserResponse.model_validate(current_user)


logger = logging.getLogger(__name__)