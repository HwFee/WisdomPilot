"""Challenge API Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChallengeBase(BaseModel):
    """Base challenge schema"""
    code: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    type: str
    difficulty: int = 1
    requirements: dict = {}
    rewards: dict = {}
    min_level: int = 0


class ChallengeSummary(ChallengeBase):
    """Challenge summary"""
    id: int
    is_active: bool = True

    model_config = {"from_attributes": True}


class ChallengeDetail(ChallengeBase):
    """Challenge detail"""
    id: int
    is_active: bool = True
    max_attempts: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserChallengeBase(BaseModel):
    """Base user challenge schema"""
    status: str
    current_progress: int
    target_value: int
    attempts: int


class UserChallengeSummary(UserChallengeBase):
    """User challenge summary"""
    id: str
    user_id: str
    challenge_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserChallengeDetail(UserChallengeSummary):
    """User challenge detail with challenge info"""
    challenge: ChallengeSummary

    model_config = {"from_attributes": True}


class ChallengeListResponse(BaseModel):
    """Response for challenge list"""
    challenges: list[ChallengeSummary]
    total: int


class ChallengeDetailResponse(BaseModel):
    """Response for single challenge"""
    challenge: ChallengeDetail


class UserChallengeResponse(BaseModel):
    """Response for user challenge"""
    user_challenge: UserChallengeSummary
    is_completed: bool


class UserChallengesResponse(BaseModel):
    """Response for user's challenges"""
    challenges: list[UserChallengeDetail]
    total: int
    completed_count: int


class ChallengeProgressResponse(BaseModel):
    challenge_id: int
    current_progress: int
    target_value: int
    is_completed: bool
    status: str
