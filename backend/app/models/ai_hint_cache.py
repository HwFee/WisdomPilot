"""AI 提示缓存模型 - 存储已购买的 AI 提示"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class AIHintCache(Base):
    """AI 提示缓存 - 用户购买后可免费再次查看"""

    __tablename__ = "ai_hint_cache"

    # 防止并发或重复插入导致同一用户对同一题的同一级别出现多条记录
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", "hint_level", name="uix_hint_cache_user_exercise_level"),
    )

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
        comment="用户 ID"
    )
    exercise_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="练习题 ID (可以是 arena exercise ID 或 chapter exercise ID)"
    )
    hint_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="提示级别: light, medium, deep"
    )
    hint_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI 生成的提示内容"
    )
    cost: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="消耗的智核数量"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User", back_populates="ai_hint_caches"
    )

    def __repr__(self) -> str:
        return f"<AIHintCache user={self.user_id[:8]}... exercise={self.exercise_id} level={self.hint_level}>"
