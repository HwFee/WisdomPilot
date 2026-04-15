"""Chapter model"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.exercise import Exercise
    from app.models.stage import Stage
    from app.models.chapter_base_question import ChapterBaseQuestion


class Chapter(Base):
    """Chapter model - represents a chapter within a course"""

    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Chapter content text")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="Display order")
    learning_objectives: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Learning objectives as JSON array"
    )
    difficulty_tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Difficulty tags like ['数组', '递归']"
    )
    skill_tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Skill tags for adaptive learning"
    )
    estimated_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        comment="Estimated completion time in minutes"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships - use lazy="noload" to prevent automatic loading
    course: Mapped["Course"] = relationship("Course", back_populates="chapters")
    exercises: Mapped[List["Exercise"]] = relationship(
        "Exercise",
        back_populates="chapter",
        order_by="Exercise.difficulty",
        lazy="noload"
    )
    stages: Mapped[List["Stage"]] = relationship(
        "Stage",
        back_populates="chapter",
        lazy="noload"
    )
    base_questions: Mapped[List["ChapterBaseQuestion"]] = relationship(
        "ChapterBaseQuestion",
        back_populates="chapter",
        order_by="ChapterBaseQuestion.order_index",
        lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Chapter {self.id}: {self.title}>"
