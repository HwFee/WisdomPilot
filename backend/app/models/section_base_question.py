"""Section Base Question model - 小节基础测试题和强化测试题

基础测试题：每小节固定数量，由 AI 预先生成存储
强化测试题：根据用户薄弱点 AI 实时生成，也存储到同一表中

重构说明：
- 原名为 chapter_base_question，现已重构为 section_base_question
- 题目现在按小节组织，而非章节
- section_id 为必填字段，确保题目与小节强关联
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.section import Section


class SectionBaseQuestion(Base):
    """小节测试题（基础题 + 强化题）

    基础测试题：每小节有固定数量（如 5 道），question_source='base'，user_id=NULL（所有用户共享）
    强化测试题：根据薄弱点 AI 生成，question_source='enhanced'，user_id=生成用户ID（仅该用户可见）

    两者共用同一个表，方便错题本统一处理。
    """

    __tablename__ = "section_base_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属小节ID"
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属章节ID（冗余字段，方便查询）"
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="所属用户ID（强化题有值，基础题为NULL表示共享）"
    )
    question_source: Mapped[str] = mapped_column(
        String(20),
        default="base",
        nullable=False,
        index=True,
        comment="题目来源: base（基础题）/ enhanced（强化题）"
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
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="题目标题（可选）"
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
    section: Mapped["Section"] = relationship("Section", back_populates="base_questions")

    # Indexes for user isolation query optimization
    __table_args__ = (
        Index("idx_section_question_user", "user_id"),
        Index("idx_section_question_section_user", "section_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<SectionBaseQuestion {self.id}: Section {self.section_id} {self.question_source} Q{self.order_index}>"

    def to_dict(self) -> dict:
        """转换为字典格式（用于 API 响应）"""
        return {
            "id": self.id,
            "section_id": self.section_id,
            "chapter_id": self.chapter_id,
            "question_source": self.question_source,
            "order_index": self.order_index,
            "type": self.question_type,
            "title": self.title,
            "text": self.question_text,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "knowledge_points": self.knowledge_points,
            "difficulty": self.difficulty,
            "code_template": self.code_template,
            "test_cases": self.test_cases,
        }


# 保持向后兼容的别名
ChapterBaseQuestion = SectionBaseQuestion
