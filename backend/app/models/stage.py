"""Stage model - 关卡模型"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.chapter import Chapter


class Stage(Base):
    """Stage model - represents a learning stage/level within a course

    关卡学习模式：
    - 每个关卡属于一门课程，可选关联章节
    - 用户需要完成指定数量练习并达到正确率
    - 完成练习后进行验证题测试
    - 通过验证后解锁下一关
    """

    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属课程ID"
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联章节ID（可选）"
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="关卡顺序"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="关卡标题"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="关卡描述"
    )
    learning_objectives: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="学习目标列表"
    )
    required_exercises: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="需完成的练习题数量"
    )
    required_accuracy: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        nullable=False,
        comment="需达到的正确率（0-1）"
    )
    verification_questions: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="验证题数量"
    )
    xp_reward: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="完成奖励经验值"
    )
    quota_bonus: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="完成奖励AI配额"
    )
    difficulty_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="关卡难度（1-8，洛谷体系: 1入门 2普及- 3普及/提高- 4普及+/提高 5提高+/省选- 6省选/NOI- 7NOI 8NOI+/CTSC）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    course: Mapped["Course"] = relationship("Course", back_populates="stages")
    chapter: Mapped[Optional["Chapter"]] = relationship("Chapter", back_populates="stages")

    def __repr__(self) -> str:
        return f"<Stage {self.id}: {self.title} (course={self.course_id}, order={self.order_index})>"
