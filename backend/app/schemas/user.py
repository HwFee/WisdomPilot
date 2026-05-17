from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("用户名不能为空")
        if len(v) < 2:
            raise ValueError("用户名至少需要2个字符")
        if len(v) > 100:
            raise ValueError("用户名不能超过100个字符")
        if not re.match(r"^[一-龥a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.

        Requirements:
        - At least 8 characters
        - At least one letter (a-z or A-Z)
        - At least one digit (0-9)
        """
        errors = []
        if len(v) < 8:
            errors.append("密码长度至少需要8个字符")
        if not re.search(r"[A-Za-z]", v):
            errors.append("密码需要包含至少一个字母")
        if not re.search(r"\d", v):
            errors.append("密码需要包含至少一个数字")

        if errors:
            raise ValueError("; ".join(errors))
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str
    remember_me: bool = False


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
