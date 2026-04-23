"""Statistics models for tracking user learning progress"""

import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class ProgressStatus(str, enum.Enum):
    """Chapter progress status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActivityType(str, enum.Enum):
    """Activity log types"""
    CHAPTER_STARTED = "chapter_started"
    CHAPTER_COMPLETED = "chapter_completed"
    SUBSECTION_COMPLETED = "subsection_completed"
    SESSION_ENDED = "session_ended"
    ACHIEVEMENT = "achievement"


class ChapterProgress(Base):
    """Tracks user's progress per chapter"""

    __tablename__ = "chapter_progress"

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
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=ProgressStatus.NOT_STARTED.value,
        nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    completed_subsections: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )
    completed_exercise_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    completed_exercises_by_subsection: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    # 存储每道题的答题结果：{chapterId}-{subsectionIndex}-{exerciseId}: "correct" | "wrong"
    exercise_results: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chapter_progress")

    def __repr__(self) -> str:
        return f"<ChapterProgress user={self.user_id} chapter={self.chapter_id} status={self.status}>"


class LearningSession(Base):
    """Tracks learning time sessions"""

    __tablename__ = "learning_sessions"

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
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    subsection_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="learning_sessions")

    def __repr__(self) -> str:
        return f"<LearningSession user={self.user_id} chapter={self.chapter_id} active={self.is_active}>"


class ActivityLog(Base):
    """Logs recent learning activities"""

    __tablename__ = "activity_logs"

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
    activity_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    subsection_index: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    extra_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog user={self.user_id} type={self.activity_type}>"
