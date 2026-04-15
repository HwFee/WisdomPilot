"""UserWeakPoint model - 薄弱点追踪"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.wrong_question import WrongQuestion


class UserWeakPoint(Base):
    """UserWeakPoint model - 用户薄弱点追踪

    用于识别用户在哪些知识点上存在困难：
    - 记录每个知识点的错误次数
    - 追踪最近错误时间
    - 记录复习次数和掌握程度
    - 用于生成针对性复习推荐
    """

    __tablename__ = "user_weak_points"

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
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID"
    )
    knowledge_point: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="知识点名称"
    )
    error_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="错误次数"
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最近错误时间"
    )
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="复习次数"
    )
    mastery_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="掌握程度（1-5，1为最薄弱）"
    )
    last_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最近复习时间"
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
    user: Mapped["User"] = relationship("User", back_populates="weak_point_records")

    def __repr__(self) -> str:
        return f"<UserWeakPoint user={self.user_id} point={self.knowledge_point} mastery={self.mastery_level}>"

    def record_error(self) -> None:
        """记录一次错误"""
        self.error_count += 1
        self.last_error_at = utc_now()
        # 错误越多，掌握程度越低（最低为1）
        if self.mastery_level > 1:
            self.mastery_level = max(1, self.mastery_level - 1)

    def record_review(self, success: bool) -> None:
        """记录一次复习

        Args:
            success: 是否成功（做对了）
        """
        self.review_count += 1
        self.last_review_at = utc_now()
        if success:
            # 复习成功，提高掌握程度（最高为5）
            self.mastery_level = min(5, self.mastery_level + 1)
            # 减少错误计数
            if self.error_count > 0:
                self.error_count -= 1

    @property
    def weakness_score(self) -> float:
        """薄弱程度评分（0-1，越高越薄弱）"""
        # 综合错误次数和掌握程度计算
        error_factor = min(1.0, self.error_count / 10)  # 错误次数因子
        mastery_factor = (6 - self.mastery_level) / 5    # 掌握程度因子（反向）
        return (error_factor + mastery_factor) / 2
