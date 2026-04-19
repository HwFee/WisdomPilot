"""
Course Mastery Model - 课程掌握度追踪

课程级掌握度，由章节聚合而成。

层级关系：
- 知识点掌握度 (KnowledgePointMastery) - 最细粒度
- 小节掌握度 (SectionMastery) - 知识点聚合
- 章节掌握度 (ChapterMastery) - 小节聚合
- 课程掌握度 (CourseMastery) - 章节聚合（最顶层）
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course


class CourseMastery(Base):
    """
    课程掌握度 - BKT 聚合最顶层

    每个用户每个课程一条记录，聚合该课程下所有章节的掌握度。
    """

    __tablename__ = "course_mastery"

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
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
        index=True
    )

    # BKT 聚合掌握度
    bkt_aggregated_p_l: Mapped[float] = mapped_column(
        Float,
        default=0.15,
        comment="BKT聚合掌握概率（课程内章节平均值）"
    )
    mastery_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="掌握度分数 0-100（= bkt_aggregated_p_l * 100）"
    )

    # 章节统计
    chapters_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="课程内章节总数"
    )
    completed_chapters_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="已完成章节数"
    )

    # 知识点统计（汇总）
    knowledge_points_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="课程涉及的知识点总数"
    )
    mastered_points_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="已掌握知识点数（P(L)>=0.95）"
    )

    # 完成状态
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否完成（所有章节掌握）"
    )

    # 时间戳
    first_practiced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_mastery"),
        Index("idx_course_mastery_user", "user_id"),
        Index("idx_course_mastery_course", "course_id"),
    )

    @property
    def is_mastered(self) -> bool:
        """是否达到掌握阈值"""
        return self.bkt_aggregated_p_l >= 0.95

    @property
    def progress_percentage(self) -> float:
        """学习进度百分比（基于已完成章节）"""
        if self.chapters_count == 0:
            return 0.0
        return (self.completed_chapters_count / self.chapters_count) * 100

    def __repr__(self) -> str:
        return f"<CourseMastery user={self.user_id[:8]}... course={self.course_id} p_l={self.bkt_aggregated_p_l:.2f}>"
