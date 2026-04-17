"""Section model - 小节模型

每个章节下的具体学习单元，用于更细粒度的学习进度追踪。
例如：第一章"C语言入门"下的小节：
  - 1.1 程序的基本结构
  - 1.2 第一个C程序
  - 1.3 编译与运行
  - 1.4 基本输入输出
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.chapter import Chapter


class Section(Base):
    """Section model - represents a section within a chapter"""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Section content text")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="Display order within chapter")
    learning_objectives: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Learning objectives as JSON array"
    )
    estimated_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
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

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="sections")

    def __repr__(self) -> str:
        return f"<Section {self.id}: {self.title}>"

    def to_dict(self) -> dict:
        """转换为字典格式（用于 API 响应）"""
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "order_index": self.order_index,
            "learning_objectives": self.learning_objectives,
            "estimated_minutes": self.estimated_minutes,
            "is_active": self.is_active,
        }
