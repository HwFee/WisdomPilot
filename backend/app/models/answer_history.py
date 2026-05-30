"""
Answer History Model - 答题历史记录

防刷分核心：记录每道题的每次作答详情。

用途：
1. 防止同一题目重复影响掌握度
2. 分析学习曲线
3. 计算知识点掌握度
4. 支持参数调优（EM算法）
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, Text, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course
    from app.models.chapter import Chapter


class AnswerHistory(Base):
    """
    答题历史记录

    记录每道题的每次作答详情，用于：
    - 防刷分检测（同一题目只计一次）
    - 学习曲线分析
    - BKT 参数调优
    """

    __tablename__ = "answer_history"

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

    # 题目标识（支持多种题目来源）
    question_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="题目来源: mastery/challenge/exercise"
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="题目ID"
    )
    exercise_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="统一题目标识，格式: source-courseId-chapterId-questionId"
    )

    # 上下文
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapters.id"),
        nullable=True,
        index=True
    )

    # 答题结果
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    user_answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="答题耗时"
    )

    # BKT 更新信息（用于调试和分析）
    p_l_before: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="答题前知识点平均掌握概率"
    )
    p_l_after: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="答题后知识点平均掌握概率"
    )
    knowledge_points_updated: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="本次更新的知识点列表"
    )

    # 防刷分核心字段
    counted_for_mastery: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否计入掌握度计算"
    )
    not_counted_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="不计入原因: duplicate_question/rate_limited/manual"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    course: Mapped[Optional["Course"]] = relationship("Course")
    chapter: Mapped[Optional["Chapter"]] = relationship("Chapter")

    __table_args__ = (
        Index("idx_answer_user_question", "user_id", "question_source", "question_id"),
        Index("idx_answer_chapter_time", "chapter_id", "created_at"),
        Index("idx_answer_user_counted", "user_id", "counted_for_mastery"),
    )

    def __repr__(self) -> str:
        status = "✓" if self.is_correct else "✗"
        counted = "计入" if self.counted_for_mastery else "不计入"
        return f"<AnswerHistory user={self.user_id[:8]} q={self.question_id} {status} {counted}>"
