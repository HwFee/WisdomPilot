"""Note model for user exercise notes"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Note(Base):
    """User's notes on exercises"""

    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    exercise_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    chapter_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    subsection_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    # 标签列表
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )
    # 关联的知识点
    knowledge_points: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )
    # 笔记来源: manual=手动创建, ai_answer=AI回答, question=题目内容
    source: Mapped[str] = mapped_column(
        String(20),
        default="manual",
        nullable=False
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
    user: Mapped["User"] = relationship("User", back_populates="notes")

    def __repr__(self) -> str:
        return f"<Note user={self.user_id} title={self.title}>"


class NoteTag(Base):
    """User's custom note tags"""

    __tablename__ = "note_tags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    color: Mapped[str] = mapped_column(
        String(20),
        default="#6366f1",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="note_tags")

    def __repr__(self) -> str:
        return f"<NoteTag user={self.user_id} name={self.name}>"
