"""Exercise model"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.chapter import Chapter
    from app.models.stage import Stage


class Exercise(Base):
    """Exercise model - represents a practice exercise

    练习题来源：
    - tk: TK题库导入
    - ai_generated: AI生成

    关联：
    - 章节（原有）
    - 关卡（新增）
    """

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属章节ID（可选，关卡练习可能不需要）"
    )
    stage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("stages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属关卡ID"
    )
    source: Mapped[str] = mapped_column(
        String(20),
        default="manual",
        comment="Source: manual, tk, ai_generated"
    )
    source_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Original question ID from external bank or AI"
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type: choice, programming, fill_blank"
    )
    difficulty: Mapped[int] = mapped_column(Integer, default=1, comment="1-8 difficulty scale (洛谷体系: 1入门 2普及- 3普及/提高- 4普及+/提高 5提高+/省选- 6省选/NOI- 7NOI 8NOI+/CTSC)")
    difficulty_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        comment="难度权重（用于验证题生成）"
    )
    knowledge_points: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="知识点标签列表"
    )
    content: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Question content: {text, options, code_template, description}"
    )
    solution: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Solution: {answer, explanation}"
    )
    test_cases: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Test cases for programming exercises"
    )
    hints: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Hint list"
    )
    skill_tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Skill tags for matching"
    )
    common_errors: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Common error patterns"
    )
    # Vector embedding for similarity search (1536 dimensions for OpenAI embeddings)
    embedding: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Vector embedding (JSON array of floats) for semantic search"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether manually verified"
    )
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_rate: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Correct rate stats: {total, correct}"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="exercises")
    stage: Mapped[Optional["Stage"]] = relationship("Stage")

    def __repr__(self) -> str:
        return f"<Exercise {self.id}: {self.type} (difficulty={self.difficulty}, source={self.source})>"
