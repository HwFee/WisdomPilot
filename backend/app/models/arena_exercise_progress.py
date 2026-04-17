"""
Arena Exercise Progress Model

Tracks user's progress on each exercise in Challenge Path (挑战之路).

Design:
- Each course has ONE challenge path per user
- Exercise records are persistent (no session concept)
- Old exercises have fixed order, new exercises get appended
- exercise_id is used for wrong question book and favorites integration
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course
    from app.models.exercise import Exercise


class ArenaExerciseProgress(Base):
    """
    Arena Exercise Progress model - tracks progress on each exercise in Challenge Path

    Key concepts:
    - One challenge path per course per user (no session needed)
    - exercise_id is stable for wrong question book / favorites / notes integration
    - exercise_index determines display order
    - Old exercises have fixed index, new exercises are appended
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

    # Exercise info - exercise_id is stable and used for cross-references
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercises.id"), nullable=False, index=True
    )
    exercise_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Exercise order (1-based). Fixed for old exercises."
    )

    # Progress status
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether submitted (regardless of correctness)"
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether answered correctly"
    )
    is_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether the exercise is accessible"
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

    __table_args__ = (
        # One exercise record per user per course per exercise
        UniqueConstraint("user_id", "course_id", "exercise_id", name="uq_arena_user_course_exercise"),
        Index("idx_arena_progress_user_course", "user_id", "course_id"),
        Index("idx_arena_progress_user_course_index", "user_id", "course_id", "exercise_index"),
    )

    def __repr__(self) -> str:
        return f"<ArenaExerciseProgress user={self.user_id} course={self.course_id} exercise={self.exercise_id} index={self.exercise_index}>"
