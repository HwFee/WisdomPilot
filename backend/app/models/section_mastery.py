"""
Section Mastery Model - 小节掌握度追踪

小节级的 BKT 掌握度，聚合后形成章节掌握度。

层级关系：
- 知识点掌握度 (KnowledgePointMastery) - 最细粒度
- 小节掌握度 (SectionMastery) - 知识点聚合
- 章节掌握度 (ChapterMastery) - 小节聚合
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from app.utils.time import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.section import Section
    from app.models.chapter import Chapter


class SectionMastery(Base):
    """
    小节掌握度 - BKT 聚合

    每个用户每个小节一条记录，聚合该小节下所有知识点的掌握度。
    """

    __tablename__ = "section_mastery"

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
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sections.id"),
        nullable=False,
        index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id"),
        nullable=False,
        index=True,
        comment="冗余存储，方便查询"
    )

    # BKT 聚合掌握度
    bkt_aggregated_p_l: Mapped[float] = mapped_column(
        Float,
        default=0.15,
        comment="BKT聚合掌握概率（小节内知识点平均值）"
    )
    mastery_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="掌握度分数 0-100（= bkt_aggregated_p_l * 100）"
    )

    # 知识点统计
    knowledge_points_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="小节涉及的知识点总数"
    )
    mastered_points_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="已掌握知识点数（P(L)>=0.95）"
    )

    # 答题统计
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="小节内总题数"
    )
    answered_questions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="已答题数"
    )
    correct_questions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="答对题数"
    )

    # 完成状态
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否完成（所有知识点掌握）"
    )

    # 时间戳
    first_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间"
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
    user: Mapped["User"] = relationship("User")
    section: Mapped["Section"] = relationship("Section")
    chapter: Mapped["Chapter"] = relationship("Chapter")

    __table_args__ = (
        UniqueConstraint("user_id", "section_id", name="uq_user_section_mastery"),
        Index("idx_section_mastery_user_chapter", "user_id", "chapter_id"),
    )

    @property
    def is_mastered(self) -> bool:
        """是否达到掌握阈值"""
        return self.bkt_aggregated_p_l >= 0.95

    def __repr__(self) -> str:
        return f"<SectionMastery user={self.user_id[:8]}... section={self.section_id} p_l={self.bkt_aggregated_p_l:.2f}>"
