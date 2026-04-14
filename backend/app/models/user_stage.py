"""UserStageProgress model - 用户关卡进度"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from enum import Enum

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.stage import Stage


class StageStatus(str, Enum):
    """关卡状态枚举"""
    LOCKED = "locked"           # 锁定，未解锁
    UNLOCKED = "unlocked"       # 已解锁，未开始
    IN_PROGRESS = "in_progress" # 进行中
    COMPLETED = "completed"     # 已完成


class UserStageProgress(Base):
    """UserStageProgress model - 用户关卡进度追踪

    追踪用户在各个关卡的进度：
    - 锁定状态：需要完成前置关卡才能解锁
    - 练习阶段：完成练习题并达到正确率要求
    - 验证阶段：通过AI生成的验证题测试
    - 完成状态：获得经验值和配额奖励
    """

    __tablename__ = "user_stage_progress"

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
    stage_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关卡ID"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=StageStatus.LOCKED.value,
        nullable=False,
        comment="状态：locked, unlocked, in_progress, completed"
    )
    exercises_completed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="已完成的练习数"
    )
    exercises_correct: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="正确的练习数"
    )
    accuracy: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="当前正确率"
    )
    verification_started: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已开始验证阶段"
    )
    verification_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否通过验证"
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="尝试次数（验证阶段）"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间"
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
    user: Mapped["User"] = relationship("User", back_populates="stage_progress")
    stage: Mapped["Stage"] = relationship("Stage")

    def __repr__(self) -> str:
        return f"<UserStageProgress user={self.user_id} stage={self.stage_id} status={self.status}>"

    def is_practice_complete(self) -> bool:
        """检查练习阶段是否完成"""
        if self.stage is None:
            return False
        return (
            self.exercises_completed >= self.stage.required_exercises
            and self.accuracy >= self.stage.required_accuracy
        )

    def can_start_verification(self) -> bool:
        """是否可以开始验证阶段"""
        return self.is_practice_complete() and not self.verification_started

    def can_advance(self) -> bool:
        """是否可以进入下一关"""
        return self.status == StageStatus.COMPLETED.value
