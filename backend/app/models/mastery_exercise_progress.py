"""
Mastery Exercise Progress Model

Tracks user's progress on each exercise in Mastery Path (精进之路).

Design:
- Each chapter has its own set of exercises (base test + enhanced test)
- Progress is tracked per chapter per question
- Supports both choice questions and programming questions
- Integrates with wrong question book via exercise_key
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course
    from app.models.chapter import Chapter


class MasteryExerciseProgress(Base):
    """
    Mastery Exercise Progress model - tracks progress on each exercise in Mastery Path

    Key concepts:
    - One progress record per user per course per chapter per question
    - question_type distinguishes base test questions from enhanced test questions
    - exercise_key is used for wrong question book integration
    """

    __tablename__ = "mastery_exercise_progress"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id"), nullable=False, index=True
    )

    # Question identifier
    question_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="Question ID within the chapter test"
    )
    question_type: Mapped[str] = mapped_column(
        String(20), default="base", comment="base=基础测试题, enhanced=强化测试题"
    )
    exercise_key: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True, comment="错题本关联key: mastery-{courseId}-{chapterId}-{questionId}"
    )

    # Question order within chapter
    question_index: Mapped[int] = mapped_column(
        Integer, default=0, comment="Question order in current chapter test"
    )

    # Progress status
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether submitted"
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether answered correctly"
    )

    # Answer storage
    user_answer: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="User's submitted answer"
    )
    correct_answer: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Correct answer snapshot"
    )

    # Code storage for programming questions
    saved_code: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Saved code for programming questions"
    )
    current_language: Mapped[str] = mapped_column(
        String(20), default="python", comment="Current language for code"
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
    chapter: Mapped["Chapter"] = relationship("Chapter")

    __table_args__ = (
        # One progress record per user per course per chapter per question
        UniqueConstraint("user_id", "course_id", "chapter_id", "question_id", "question_type",
                         name="uq_mastery_user_chapter_question"),
        Index("idx_mastery_progress_user_chapter", "user_id", "chapter_id"),
        Index("idx_mastery_progress_user_course", "user_id", "course_id"),
    )

    def __repr__(self) -> str:
        return f"<MasteryExerciseProgress user={self.user_id} chapter={self.chapter_id} question={self.question_id}>"
