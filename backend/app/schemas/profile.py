"""Profile API Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    username: str
    xp: int
    level: int
    streak_days: int
    last_activity_date: datetime
    preferred_languages: list[str]
    total_exercises: int
    correct_exercises: int
    accuracy_rate: float
    is_admin: bool
    ai_quota: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """Update profile request"""
    preferred_languages: Optional[list[str]] = None


class AddXpRequest(BaseModel):
    """Add XP request"""
    xp_amount: int


class CheckinResponse(BaseModel):
    """Check-in response"""
    streak_days: int
    checked_in_today: bool
    xp_earned: int
    last_checkin_date: Optional[datetime] = None


class CheckinStatusResponse(BaseModel):
    """Check-in status response"""
    streak_days: int
    checked_in_today: bool
    last_checkin_date: Optional[datetime] = None
