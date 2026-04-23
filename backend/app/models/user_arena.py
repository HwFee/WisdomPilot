"""
User Arena Profile Model

Tracks user's competitive profile for the Challenge Path (挑战之路).
Global profile - independent of courses.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


# Tier thresholds
TIER_THRESHOLDS = {
    "bronze": 0,
    "silver": 1000,
    "gold": 2500,
    "platinum": 5000,
    "diamond": 10000,
}


class UserArenaProfile(Base):
    """
    User Arena Profile model - tracks user's competitive stats for Challenge Path.
    One profile per user (global, not per-course).
    """

    __tablename__ = "user_arena_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # Competitive score
    total_score: Mapped[float] = mapped_column(Float, default=0.0, comment="Total accumulated score")
    tier: Mapped[str] = mapped_column(String(20), default="bronze", comment="Current tier")
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Current rank in leaderboard")

    # Tier system
    sub_tier: Mapped[int] = mapped_column(Integer, default=4, comment="Sub-tier (1=I, 2=II, 3=III, 4=IV, 5=V)")
    stars: Mapped[int] = mapped_column(Integer, default=0, comment="Current stars")
    protection_remaining: Mapped[int] = mapped_column(Integer, default=3, comment="Remaining tier protection uses")
    highest_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="Historical highest tier")
    highest_sub_tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Historical highest sub-tier")

    # Challenge statistics
    total_challenges: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0, comment="Challenges with >= 80% correct")
    losses: Mapped[int] = mapped_column(Integer, default=0, comment="Challenges with < 50% correct")

    # Performance metrics
    highest_difficulty: Mapped[int] = mapped_column(Integer, default=0, comment="Highest difficulty completed")
    best_streak: Mapped[int] = mapped_column(Integer, default=0, comment="Best consecutive correct streak")
    current_streak: Mapped[int] = mapped_column(Integer, default=0, comment="Current consecutive correct streak")
    avg_accuracy: Mapped[float] = mapped_column(Float, default=0.0, comment="Average accuracy across challenges")

    # Hybrid recommendation fields
    behavior_embedding: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="User behavior embedding (JSON array) for hybrid recommendation"
    )
    avg_time_spent: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Average time spent per exercise in seconds"
    )
    total_submissions: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total submission count"
    )

    # Time tracking
    total_time_spent: Mapped[int] = mapped_column(Integer, default=0, comment="Total time in seconds")
    last_challenge_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_arena"),
        Index("idx_arena_user", "user_id"),
        Index("idx_arena_score", "total_score"),
    )

    def __repr__(self) -> str:
        return f"<UserArenaProfile user={self.user_id} tier={self.tier} score={self.total_score}>"
