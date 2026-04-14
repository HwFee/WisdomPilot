"""Achievement model - represents badges/achievements users can earn"""

import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class AchievementType(str, enum.Enum):
    """Achievement types"""
    LESSON_COMPLETE = "lesson_complete"
    COURSE_COMPLETE = "course_complete"
    STREAK = "streak"
    ACCURACY = "accuracy"
    SPEED = "speed"
    EXPLORER = "explorer"
    CHALLENGE = "challenge"
    SPECIAL = "special"


class Achievement(Base):
    """Achievement model - represents badges/achievements users can earn"""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique achievement code"
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Icon name or emoji"
    )
    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Achievement type from AchievementType enum"
    )
    category: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Category: learning, speed, exploration, etc."
    )
    xp_reward: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="XP reward for earning this achievement"
    )
    quota_reward: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Quota bonus for earning this achievement"
    )
    requirements: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Requirements to unlock: {threshold: 10, type: 'streak'}"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_secret: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Secret achievements don't show until earned"
    )
    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Difficulty level 1-5"
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Order for display"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="achievement"
    )

    def __repr__(self) -> str:
        return f"<Achievement {self.code}: {self.title}>"


class UserAchievement(Base):
    """Tracks which achievements a user has earned"""

    __tablename__ = "user_achievements"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    achievement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("achievements.id"),
        nullable=False,
        index=True
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current progress toward achievement"
    )
    is_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has been notified"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship("Achievement", back_populates="user_achievements")

    def __repr__(self) -> str:
        return f"<UserAchievement user={self.user_id} achievement={self.achievement_id}>"
