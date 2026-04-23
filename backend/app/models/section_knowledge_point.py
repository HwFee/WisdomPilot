"""Section Knowledge Point Model - 小节知识点内容模型

每个小节包含多个知识点，每个知识点有：
- 标题
- 内容讲解
- 代码示例
- 难度等级

用户学习小节时，按知识点顺序展示内容，然后做题测试。
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.section import Section


class SectionKnowledgePoint(Base):
    """小节知识点内容

    存储每个知识点的学习内容，用户学习后做题测试。
    """

    __tablename__ = "section_knowledge_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属小节ID"
    )

    # 知识点基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="知识点名称"
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="显示顺序"
    )

    # 内容
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="知识点讲解内容（Markdown格式）"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="知识点简要总结"
    )

    # 代码示例
    code_example: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="代码示例"
    )
    code_language: Mapped[str] = mapped_column(
        String(20),
        default="c",
        comment="代码语言"
    )
    code_explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="代码示例解释"
    )

    # 难度和重要程度
    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="难度等级 1-5"
    )
    importance: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="重要程度 1-5"
    )

    # 相关知识点
    related_points: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="相关知识点列表"
    )

    # 学习提示
    tips: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="学习提示列表"
    )

    # 常见错误
    common_mistakes: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="常见错误列表"
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
    section: Mapped["Section"] = relationship("Section", back_populates="knowledge_points")

    __table_args__ = (
        Index("idx_skp_section_order", "section_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<SectionKnowledgePoint {self.id}: {self.name}>"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "section_id": self.section_id,
            "name": self.name,
            "order_index": self.order_index,
            "content": self.content,
            "summary": self.summary,
            "code_example": self.code_example,
            "code_language": self.code_language,
            "code_explanation": self.code_explanation,
            "difficulty": self.difficulty,
            "importance": self.importance,
            "related_points": self.related_points or [],
            "tips": self.tips or [],
            "common_mistakes": self.common_mistakes or [],
        }
