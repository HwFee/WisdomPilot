"""
Chapter Mastery Model

Tracks user's mastery level for each chapter they've studied.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chapter import Chapter
    from app.models.course import Course


class ChapterMastery(Base):
    """
    Chapter Mastery model - tracks user's progress in each chapter

    Key features:
    - Unique constraint: one mastery record per user per chapter
    - Multiple score components for detailed analysis
    - Learning objectives tracking
    """

    __tablename__ = "chapter_mastery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("chapters.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)

    # Mastery scores (0-100)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    mastery_level: Mapped[str] = mapped_column(String(20), default="入门")

    # Component scores for analysis
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    depth_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Statistics
    total_exercises: Mapped[int] = mapped_column(Integer, default=0)
    correct_exercises: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, default=0)

    # BKT 相关字段
    bkt_aggregated_p_l: Mapped[float] = mapped_column(
        Float,
        default=0.15,
        comment="BKT聚合掌握概率（章节内知识点平均值）"
    )
    knowledge_points_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="章节涉及的知识点总数"
    )
    mastered_points_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="已掌握知识点数（P(L)>=0.95）"
    )

    # Learning objectives status: {"objective1": true, "objective2": false, ...}
    objectives_status: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    first_practiced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mastered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chapter_masteries")
    chapter: Mapped["Chapter"] = relationship("Chapter")
    course: Mapped["Course"] = relationship("Course")

    __table_args__ = (
        UniqueConstraint("user_id", "chapter_id", name="uq_user_chapter_mastery"),
        Index("idx_mastery_user", "user_id"),
        Index("idx_mastery_chapter", "chapter_id"),
        Index("idx_mastery_course_score", "course_id", "mastery_score"),
    )

    def __repr__(self) -> str:
        return f"<ChapterMastery user={self.user_id} chapter={self.chapter_id} score={self.mastery_score}>"
