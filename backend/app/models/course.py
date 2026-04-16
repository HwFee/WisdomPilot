"""Course model"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.chapter import Chapter


class Course(Base):
    """Course model - represents a programming course

    支持的8门课程：
    - C, C++, Python, Java, Rust
    - 数据结构与算法 (DSA)
    - 算法设计与分析 (ADA)
    - 离散数学 (DiscreteMath)
    """

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Course code: C, C++, Python, Java, Rust, DSA, ADA, DiscreteMath"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1, comment="1-5 difficulty scale")
    icon: Mapped[str] = mapped_column(String(100), nullable=True, comment="Icon identifier")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships - use lazy="noload" to prevent automatic loading
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter",
        back_populates="course",
        order_by="Chapter.order_index",
        lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Course {self.code}: {self.name}>"
