"""Exercise Generation Session - 题目生成会话模型"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExerciseGenerationSession(Base):
    """题目生成会话 - 用于流式生成跟踪"""

    __tablename__ = "exercise_generation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # 会话类型: "enhanced"(强化测试) | "challenge"(挑战之路)
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # 关联的section/chapter
    section_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chapter_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    course_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 生成请求参数
    request_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # 生成状态
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_exercises: Mapped[list] = mapped_column(JSON, default=list)

    # 会话状态: generating | completed | failed
    status: Mapped[str] = mapped_column(String(20), default="generating")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1)
    )

    # 关联
    user = relationship("User", back_populates="generation_sessions")

    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now(timezone.utc) > self.expires_at

    def add_exercise(self, exercise: dict) -> None:
        """添加一道生成的题目（按 index 有序插入）

        注意：JSON 列不会自动检测列表内部变更，必须重新赋值整个列表。
        按 exercise['index'] 排序，确保顺序与生成请求一致。
        """
        new_list = self.generated_exercises + [exercise]
        # 按 index 排序（若 exercise 无 index，则放在末尾）
        new_list.sort(key=lambda e: e.get("index", 9999))
        self.generated_exercises = new_list
        self.generated_count = len(self.generated_exercises)
        self.updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """标记生成为完成"""
        self.status = "completed"
        self.updated_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """标记生成为失败"""
        self.status = "failed"
        self.error_message = error
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "session_type": self.session_type,
            "total_count": self.total_count,
            "generated_count": self.generated_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
