"""Chapter Base Question model - 章节基础测试题

每章节的固定基础测试题，由 AI 生成后存储。
用于在用户学习完知识点后进行基础测试。
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.chapter import Chapter


class ChapterBaseQuestion(Base):
    """章节基础测试题

    每章节有固定数量的基础题（如 3-5 道）。
    题目由 AI 生成，超级基础，仅测试知识点掌握。
    生成后固定存储，用于客观评估用户水平。
    """

    __tablename__ = "chapter_base_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属章节ID"
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="题目顺序（第几题）"
    )
    question_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="choice",
        comment="题目类型: choice, programming, fill_blank"
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="题目内容"
    )
    options: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="选择题选项列表"
    )
    correct_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="正确答案（选择题为选项字母如'A'，编程题为代码）"
    )
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="答案解析"
    )
    knowledge_points: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="考查的知识点列表"
    )
    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="难度（基础题固定为 1-2）"
    )
    code_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="编程题代码模板"
    )
    test_cases: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="编程题测试用例"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="base_questions")

    def __repr__(self) -> str:
        return f"<ChapterBaseQuestion {self.id}: Chapter {self.chapter_id} Q{self.order_index}>"

    def to_dict(self) -> dict:
        """转换为字典格式（用于 API 响应）"""
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "order_index": self.order_index,
            "type": self.question_type,
            "text": self.question_text,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "knowledge_points": self.knowledge_points,
            "difficulty": self.difficulty,
            "code_template": self.code_template,
            "test_cases": self.test_cases,
        }
