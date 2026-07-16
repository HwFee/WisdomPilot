"""SpacedRepetition model - 间隔复习调度"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.exercise import Exercise


# 默认复习间隔（天数）
DEFAULT_INTERVALS = [1, 3, 7, 14, 30]


class SpacedRepetition(Base):
    """SpacedRepetition model - 间隔复习调度

    基于艾宾浩斯遗忘曲线的间隔复习系统：
    - 追踪每道题的复习状态
    - 动态调整复习间隔
    - 根据用户表现调整难度因子

    复习时间点：
    - 第1次：学习后 1 天
    - 第2次：学习后 3 天
    - 第3次：学习后 7 天
    - 第4次：学习后 14 天
    - 第5次：学习后 30 天
    """

    __tablename__ = "spaced_repetitions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    exercise_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="练习题ID（可能为空，使用 exercise_key 作为备选标识）",
    )
    exercise_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="练习题标识（格式：chapterId-subsectionIndex-exerciseId，用于前端硬编码习题）",
    )
    stage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="关联关卡ID（已弃用，保留用于数据迁移）",
    )
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, comment="下次复习时间"
    )
    review_interval: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="当前复习间隔（天）"
    )
    ease_factor: Mapped[float] = mapped_column(
        Float, default=2.5, nullable=False, comment="难度因子（SM-2算法）"
    )
    review_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="已复习次数"
    )
    last_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最近复习时间"
    )
    last_review_result: Mapped[Optional[int]] = mapped_column(
        Integer,  # SQLite没有Boolean类型，用Integer模拟
        nullable=True,
        comment="最近复习结果（1=成功，0=失败）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="spaced_repetitions")
    exercise: Mapped["Exercise"] = relationship("Exercise")

    def __repr__(self) -> str:
        return f"<SpacedRepetition user={self.user_id} exercise={self.exercise_id} next={self.next_review_at}>"

    def calculate_next_review(self, quality: int) -> None:
        """计算下次复习时间（基于SM-2算法简化版）

        Args:
            quality: 回忆质量（0-5）
                0-2: 失败，需要重新学习
                3-5: 成功，继续复习
        """
        if quality < 3:
            # 失败：重置间隔
            self.review_interval = 1
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        else:
            # 成功：根据复习次数确定间隔
            if self.review_count == 0:
                self.review_interval = DEFAULT_INTERVALS[0]  # 1天
            elif self.review_count == 1:
                self.review_interval = DEFAULT_INTERVALS[1]  # 3天
            elif self.review_count == 2:
                self.review_interval = DEFAULT_INTERVALS[2]  # 7天
            elif self.review_count == 3:
                self.review_interval = DEFAULT_INTERVALS[3]  # 14天
            else:
                self.review_interval = DEFAULT_INTERVALS[4]  # 30天

            # 根据难度因子微调
            self.review_interval = int(self.review_interval * self.ease_factor / 2.5)

            # 提高质量因子
            self.ease_factor = min(3.0, self.ease_factor + 0.1)

        # 设置下次复习时间
        self.next_review_at = utc_now() + timedelta(days=self.review_interval)
        self.review_count += 1
        self.last_review_at = utc_now()
        self.last_review_result = 1 if quality >= 3 else 0

    @classmethod
    def create_new(
        cls, user_id: str, exercise_id: int, stage_id: Optional[int] = None
    ) -> "SpacedRepetition":
        """创建新的复习记录"""
        return cls(
            user_id=user_id,
            exercise_id=exercise_id,
            stage_id=stage_id,
            next_review_at=utc_now() + timedelta(days=DEFAULT_INTERVALS[0]),
            review_interval=DEFAULT_INTERVALS[0],
            ease_factor=2.5,
            review_count=0,
        )

    @property
    def is_due(self) -> bool:
        """是否到期需要复习"""
        return utc_now() >= self.next_review_at

    @property
    def days_overdue(self) -> int:
        """逾期天数"""
        delta = utc_now() - self.next_review_at
        return max(0, delta.days)
