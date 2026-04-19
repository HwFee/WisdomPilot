"""
Core (智核) Schemas - Request/Response models for core currency system
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CoreSpendCategory(str, Enum):
    """Valid categories for spending cores"""
    AI_HINT_LIGHT = "ai_hint_light"
    AI_HINT_MEDIUM = "ai_hint_medium"
    AI_HINT_DEEP = "ai_hint_deep"


class CoreEarnCategory(str, Enum):
    """Valid categories for earning cores"""
    MASTERY = "mastery"
    ARENA = "arena"
    CHECKIN = "checkin"
    STUDY_TIME = "study_time"
    DAILY_EXERCISES = "daily_exercises"
    DAILY_ACCURACY = "daily_accuracy"
    BONUS = "bonus"


class CoreBalanceResponse(BaseModel):
    """Response for core balance endpoint"""
    balance: int = Field(..., description="Current core balance")
    total_earned: int = Field(..., description="Total cores earned")
    total_spent: int = Field(..., description="Total cores spent")


class CoreSpendRequest(BaseModel):
    """Request for spending cores"""
    amount: int = Field(..., gt=0, le=1000, description="Amount of cores to spend (max 1000)")
    category: CoreSpendCategory = Field(..., description="Category of spending")
    reference_type: Optional[str] = Field(None, description="Reference type (exercise, etc.)")
    reference_id: Optional[str] = Field(None, description="Reference ID")
    description: Optional[str] = Field(None, description="Description of the transaction")


class CoreSpendResponse(BaseModel):
    """Response after spending cores"""
    success: bool = Field(..., description="Whether the spend was successful")
    balance_after: int = Field(..., description="Balance after spending")
    transaction_id: str = Field(..., description="ID of the transaction")


class CoreTransactionResponse(BaseModel):
    """Response for a single core transaction"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = Field(..., description="'earn' or 'spend'")
    category: str
    amount: int
    balance_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class CoreTransactionListResponse(BaseModel):
    """Response for transaction history"""
    transactions: list[CoreTransactionResponse]
    total: int = Field(..., description="Total number of transactions")


class DailyCoreSummaryResponse(BaseModel):
    """Response for daily core statistics"""
    earned_today: int = Field(..., description="Cores earned today")
    spent_today: int = Field(..., description="Cores spent today")
    daily_exercises: int = Field(..., description="Number of exercises completed today (challenge path)")
    daily_accuracy: float = Field(..., description="Today's accuracy rate (percentage)")
    pending_rewards: dict = Field(
        default_factory=dict,
        description="Pending rewards to claim (exercise count, accuracy, time)"
    )


class CoreEarnRequest(BaseModel):
    """Request for earning cores (internal use)"""
    amount: int = Field(..., gt=0, description="Amount of cores to earn")
    category: CoreEarnCategory = Field(..., description="Category of earning")
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None


class CoreEarnResponse(BaseModel):
    """Response after earning cores"""
    success: bool
    balance_after: int
    transaction_id: str
