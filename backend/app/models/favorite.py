"""Favorite model for user exercise favorites - 完全依照 WrongQuestion 格式"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Favorite(Base):
    """User's favorite exercises - 完全依照 WrongQuestion 结构

    存储完整信息快照，与错题本一致：
    - exercise_key: 题目标识（格式与错题本一致）
    - exercise_id: 原始练习题ID
    - course_id: 课程ID
    - chapter_id: 章节ID
    - exercise_content: 题目内容快照
    - exercise_type: 题目类型
    - exercise_difficulty: 题目难度
    - knowledge_points: 知识点
    - source_type/source_label: 通过 exercise_key 推断，与错题本一致
    """

    __tablename__ = "favorites"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    # 与错题本完全一致的字段
    exercise_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="练习题ID（可能为空，使用 exercise_key 作为备选标识）"
    )
    exercise_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="练习题标识: mastery-{courseId}-{chapterId}-{exerciseId} 或 arena-{courseId}-{exerciseId}"
    )
    course_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="课程ID"
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        Integer,
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
    knowledge_points: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="知识点标签列表"
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
    # 收藏夹特有字段
    folder: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="收藏夹分类名称"
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="笔记"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")

    # 与错题本完全一致的属性方法
    @property
    def source_type(self) -> str:
        """题目来源类型: mastery(精进之路), arena(挑战之路), enhanced(强化测试)"""
        if not self.exercise_key:
            return "unknown"
        if self.exercise_key.startswith("mastery-"):
            return "mastery"
        elif self.exercise_key.startswith("arena-"):
            return "arena"
        elif self.exercise_key.startswith("enhanced-"):
            return "enhanced"
        return "unknown"

    @property
    def source_label(self) -> str:
        """题目来源中文标签"""
        labels = {
            "mastery": "精进之路",
            "arena": "挑战之路",
            "enhanced": "强化测试",
            "unknown": "未知来源"
        }
        return labels.get(self.source_type, "未知来源")

    @property
    def question_title(self) -> str:
        """题目标题/摘要"""
        if not self.exercise_content:
            type_labels = {
                "choice": "选择题",
                "programming": "编程题",
                "fill_blank": "填空题",
                "fill": "填空题",
                "output": "输出题",
            }
            return type_labels.get(self.exercise_type, f"{self.exercise_type}题")
        # 尝试从 content 中提取标题
        if "title" in self.exercise_content:
            return self.exercise_content["title"]
        if "text" in self.exercise_content:
            text = self.exercise_content["text"]
            # 截取前50个字符作为标题
            if len(text) > 50:
                return text[:50] + "..."
            return text
        type_labels = {
            "choice": "选择题",
            "programming": "编程题",
            "fill_blank": "填空题",
            "fill": "填空题",
            "output": "输出题",
        }
        return type_labels.get(self.exercise_type, f"{self.exercise_type}题")

    def __repr__(self) -> str:
        return f"<Favorite user={self.user_id} key={self.exercise_key}>"
