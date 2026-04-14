"""Challenge model - represents learning challenges/levels"""

import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user_challenge import UserChallenge


class ChallengeType(str, enum.Enum):
    """Challenge types"""
    CHAPTER_COMPLETE = "chapter_complete"
    EXERCISE_COUNT = "exercise_count"
    STREAK = "streak"
    TIME_SPENT = "time_spent"
    ACCURACY = "accuracy"
    COURSE_COMPLETE = "course_complete"


class Challenge(Base):
    """Challenge model - represents a learning challenge or level"""

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique challenge code"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Challenge type from ChallengeType enum"
    )
    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Difficulty level 1-5"
    )
    # Challenge requirements (JSON) - e.g., {"chapter_id": 1, "exercise_count": 10}
    requirements: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    # Challenge rewards (JSON) - e.g., {"quota_bonus": 50, "xp": 100}
    rewards: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    min_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Minimum user level required"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Max attempts (0 = unlimited)"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    user_challenges: Mapped[list["UserChallenge"]] = relationship(
        "UserChallenge", back_populates="challenge"
    )

    def __repr__(self) -> str:
        return f"<Challenge {self.id}: {self.code}>"
