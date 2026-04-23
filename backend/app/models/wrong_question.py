"""WrongQuestion model - 错题记录"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING, Any

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.exercise import Exercise


class WrongQuestion(Base):
    """WrongQuestion model - 错题记录

    用于记录用户在练习或挑战中回答错误的题目：
    - 问题ID、用户答案、正确答案
    - 章节、知识点标签
    - 错误时间、错误次数（同题多个错误总数）
    - 去重逻辑：相同题目只记录一次，但更新错误次数和最近错误时间
    """

    __tablename__ = "wrong_questions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    exercise_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="练习题ID（可能为空，使用 exercise_key 作为备选标识）"
    )
    exercise_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="练习题标识（格式：chapterId-subsectionIndex-exerciseId，用于前端硬编码习题）"
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="课程ID"
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="章节ID"
    )
    section_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="小节ID（强化测试来源）"
    )
    stage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="关卡ID（已弃用，保留用于数据迁移）"
    )
    challenge_session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("challenge_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="挑战会话ID（挑战之路来源）"
    )
    knowledge_points: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="知识点标签列表"
    )
    user_answer: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        comment="用户答案"
    )
    correct_answer: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        comment="正确答案"
    )
    exercise_content: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="题目内容快照（题目可能被修改或删除）"
    )
    exercise_type: Mapped[str] = mapped_column(
        String(20),
        default="choice",
        comment="题目类型: choice, programming, fill_blank"
    )
    exercise_difficulty: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="题目难度"
    )
    error_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="错误次数（同题重复错误的总数）"
    )
    is_resolved: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否已解决（答对过一次）"
    )
    first_error_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
        comment="首次错误时间"
    )
    last_error_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        comment="最近错误时间"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="解决时间（首次答对时间）"
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
    user: Mapped["User"] = relationship("User", back_populates="wrong_questions")
    exercise: Mapped["Exercise"] = relationship("Exercise")

    def __repr__(self) -> str:
        return f"<WrongQuestion user={self.user_id} exercise={self.exercise_id} errors={self.error_count}>"

    def record_error(self) -> None:
        """记录一次新的错误"""
        self.error_count += 1
        self.last_error_at = utc_now()
        # 错误后标记为未解决
        self.is_resolved = False
        self.resolved_at = None

    def mark_resolved(self) -> None:
        """标记为已解决（答对过一次）"""
        if not self.is_resolved:
            self.is_resolved = True
            self.resolved_at = utc_now()

    @property
    def days_since_last_error(self) -> int:
        """距离上次错误的天数"""
        delta = utc_now() - self.last_error_at
        return delta.days

    @property
    def priority_score(self) -> float:
        """复习优先级评分（越高越需要复习）"""
        # 基于错误次数和未解决状态
        error_factor = min(2.0, self.error_count / 5)  # 最多2倍权重
        unresolved_factor = 1.5 if not self.is_resolved else 0.5
        # 时间衰减因子（越久远越需要复习）
        days_factor = min(1.0, self.days_since_last_error / 30)
        return error_factor * unresolved_factor * (1 + days_factor)
