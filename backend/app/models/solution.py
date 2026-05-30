"""Solution model - 题解模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class Solution(Base):
    """题解模型 - 用于题解广场功能"""

    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, default="", comment="内容")
    problem_link = Column(String(500), nullable=True, comment="题目链接")
    tags = Column(JSON, default=lambda: [], comment="标签列表")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    is_announcement = Column(Boolean, default=False, comment="是否为公告")
    view_count = Column(Integer, default=0, comment="浏览数")
    like_count = Column(Integer, default=0, comment="点赞数")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
