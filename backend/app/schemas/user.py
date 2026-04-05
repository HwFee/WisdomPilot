from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (public info)"""
    id: str
    is_active: bool
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for decoded token data"""
    user_id: str | None = None
    email: str | None = None


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr
