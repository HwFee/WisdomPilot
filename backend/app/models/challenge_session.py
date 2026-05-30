"""
Challenge Session Model

Tracks user's challenge sessions for the Challenge Path (竞技之路).
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course


class ChallengeSession(Base):
    """
    Challenge Session model - tracks a challenge attempt

    A session represents one complete challenge attempt with:
    - Selected exercises
    - Time limit
    - Scoring and results
    """

    __tablename__ = "challenge_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)

    # Challenge configuration
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, comment="1-5 difficulty")
    exercise_ids: Mapped[list] = mapped_column(JSON, nullable=False, comment="List of exercise IDs")
    time_limit: Mapped[int] = mapped_column(Integer, nullable=False, comment="Time limit in seconds")
    score_multiplier: Mapped[float] = mapped_column(Float, default=1.0, comment="Score multiplier based on difficulty")

    # Results
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    time_spent: Mapped[int] = mapped_column(Integer, default=0, comment="Actual time spent in seconds")
    base_score: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Bonus tracking
    time_bonus: Mapped[float] = mapped_column(Float, default=0.0)
    streak_bonus: Mapped[float] = mapped_column(Float, default=0.0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0, comment="Max consecutive correct")

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="pending, in_progress, completed, abandoned"
    )
    session_type: Mapped[str] = mapped_column(
        String(20),
        default="challenge",
        comment="challenge (timed mode) | infinite (endless mode)"
    )
    current_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Current exercise index (0-based) for infinite mode"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")

    __table_args__ = (
        Index("idx_challenge_user", "user_id"),
        Index("idx_challenge_course", "course_id"),
        Index("idx_challenge_score", "course_id", "final_score"),
        Index("idx_challenge_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ChallengeSession user={self.user_id} difficulty={self.difficulty_level} score={self.final_score}>"
