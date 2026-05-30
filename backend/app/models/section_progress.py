"""SectionProgress model - 小节学习进度追踪"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.section import Section


class SectionProgress(Base):
    """SectionProgress model - 记录用户的小节学习进度

    用于追踪用户在每个小节的学习进度：
    - 是否完成
    - 最后学习位置（内容/测试）
    - 完成时间
    """

    __tablename__ = "section_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="小节ID"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否完成"
    )
    last_position: Mapped[str] = mapped_column(
        String(20),
        default="content",
        nullable=False,
        comment="最后学习位置: content(内容) 或 quiz(测试)"
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
    section: Mapped["Section"] = relationship("Section")

    def __repr__(self) -> str:
        return f"<SectionProgress user={self.user_id} section={self.section_id} completed={self.is_completed}>"

    def mark_completed(self) -> None:
        """标记为已完成"""
        self.is_completed = True
        self.completed_at = utc_now()
