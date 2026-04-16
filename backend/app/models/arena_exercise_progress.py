"""
Arena Exercise Progress Model

Tracks user's progress on each exercise in Arena infinite mode.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course
    from app.models.exercise import Exercise
    from app.models.challenge_session import ChallengeSession


class ArenaExerciseProgress(Base):
    """
    Arena Exercise Progress model - tracks progress on each exercise in infinite mode

    Records:
    - Whether the exercise has been completed/submitted
    - Whether the answer was correct
    - Saved code for each language
    - Attempt history
    """

    __tablename__ = "arena_exercise_progress"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("challenge_sessions.id"), nullable=True, index=True
    )

    # Exercise info
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercises.id"), nullable=False, index=True
    )
    exercise_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Exercise order in session (1-based)"
    )

    # Progress status
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether submitted (regardless of correctness)"
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether answered correctly"
    )
    is_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether the exercise is accessible"
    )

    # Code storage by language - {"python": "code...", "cpp": "code..."}
    saved_codes: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="Saved code per language"
    )
    current_language: Mapped[str] = mapped_column(
        String(20), default="python", comment="Current language being used"
    )

    # Timestamps
    first_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    correct_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Time when first answered correctly"
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total submission attempts"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")
    exercise: Mapped["Exercise"] = relationship("Exercise")
    session: Mapped[Optional["ChallengeSession"]] = relationship("ChallengeSession")

    __table_args__ = (
        Index("idx_arena_progress_user_course", "user_id", "course_id"),
        Index("idx_arena_progress_session", "session_id"),
        Index("idx_arena_progress_exercise", "exercise_id"),
    )

    def __repr__(self) -> str:
        return f"<ArenaExerciseProgress user={self.user_id} exercise={self.exercise_id} correct={self.is_correct}>"
