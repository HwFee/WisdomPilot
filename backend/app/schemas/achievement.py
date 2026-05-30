"""Achievement API Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AchievementBase(BaseModel):
    """Base achievement schema"""
    code: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    type: str
    category: str
    xp_reward: int = 0
    quota_reward: int = 0
    requirements: dict = {}
    is_secret: bool = False
    difficulty: int = 1


class AchievementSummary(AchievementBase):
    """Achievement summary for lists"""
    id: int
    is_active: bool = True
    display_order: int = 0

    model_config = {"from_attributes": True}


class AchievementDetail(AchievementBase):
    """Achievement detail"""
    id: int
    is_active: bool = True
    display_order: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class AchievementWithEarned(AchievementSummary):
    """Achievement with earned status"""
    earned: bool = False
    earned_at: Optional[datetime] = None
    progress: int = 0

    model_config = {"from_attributes": True}


class UserAchievementSummary(BaseModel):
    """User achievement summary"""
    id: str
    user_id: str
    achievement_id: int
    earned_at: datetime
    progress: int
    is_notified: bool

    model_config = {"from_attributes": True}


class UserAchievementDetail(UserAchievementSummary):
    """User achievement with achievement info"""
    achievement: AchievementSummary

    model_config = {"from_attributes": True}


class AchievementListResponse(BaseModel):
    """Response for achievement list"""
    achievements: list[AchievementSummary]
    total: int


class AchievementWithEarnedResponse(BaseModel):
    """Response for achievements with earned status"""
    achievements: list[AchievementWithEarned]
    total: int
    earned_count: int


class UserAchievementsResponse(BaseModel):
    """Response for user's achievements"""
    achievements: list[UserAchievementDetail]
    total: int
    earned_count: int


class UserRankResponse(BaseModel):
    """Response for user's rank on leaderboard"""
    rank: int
    user_id: str
    username: str
    level: str  # Mastery level: 入门/学习/练习/熟练/精通
    xp: int
    streak_days: int
    accuracy_rate: float
    total_users: int
