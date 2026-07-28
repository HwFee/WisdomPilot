from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.auth.models import User
from app.auth.schemas import UserCreate, UserLogin, Token, UserResponse
from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.config import get_settings
from app.auth.errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)

settings = get_settings()


class AuthService:
    """Authentication service handling user registration and login"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate) -> tuple[User, Token]:
        """Register a new user and return user + token"""
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(
                or_(User.email == user_data.email, User.username == user_data.username)
            )
        )
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.email == user_data.email:
                raise EmailAlreadyRegisteredError
            raise UsernameAlreadyRegisteredError

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

        self.db.add(new_user)
        await self.db.flush()
        await self.db.refresh(new_user)

        # Generate token
        access_token = create_access_token(
            data={"sub": new_user.id, "email": new_user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        user_response = UserResponse.model_validate(new_user)
        token = Token(access_token=access_token, user=user_response)

        return new_user, token

    async def login(self, login_data: UserLogin) -> tuple[User, Token]:
        """Authenticate user and return user + token"""
        result = await self.db.execute(
            select(User).where(
                or_(User.email == login_data.username, User.username == login_data.username)
            )
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveAccountError

        # Use longer expiration if remember_me is True
        if login_data.remember_me:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER)
        else:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=expires_delta,
        )

        user_response = UserResponse.model_validate(user)
        token = Token(access_token=access_token, user=user_response)

        return user, token

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def forgot_password(self, email: str) -> None:
        """Look up a reset recipient without revealing whether it exists."""
        await self.db.execute(select(User.id).where(User.email == email))
        # Password-reset delivery is not configured in this application yet.
        return None
