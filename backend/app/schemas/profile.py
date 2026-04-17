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
    total_checkin_days: int = 0
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
    total_checkin_days: int = 0
    streak_multiplier: float = 1.0
    new_achievements: list[str] = []


class CheckinStatusResponse(BaseModel):
    """Check-in status response"""
    streak_days: int
    checked_in_today: bool
    last_checkin_date: Optional[datetime] = None
    total_checkin_days: int = 0


class CheckinDetailsResponse(BaseModel):
    """Check-in details response with lunar calendar info"""
    date: str
    lunar_str: str
    solar_term_str: str
    holiday_str: str
    streak_days: int
    total_checkin_days: int
    streak_multiplier: float
    checked_in_today: bool


class CheckinStatsResponse(BaseModel):
    """Check-in statistics response"""
    streak_days: int
    total_checkin_days: int
    streak_multiplier: float
    checked_in_today: bool
    next_tier_days: Optional[int] = None  # Days until next streak multiplier tier
