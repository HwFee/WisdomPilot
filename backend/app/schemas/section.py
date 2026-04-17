"""Section schemas - 小节相关的请求/响应模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SectionSummary(BaseModel):
    """小节摘要 - 用于列表显示"""
    id: int
    chapter_id: int
    title: str
    description: Optional[str] = None
    order_index: int
    estimated_minutes: int = Field(default=15, description="预计学习时间（分钟）")
    is_completed: bool = Field(default=False, description="用户是否已完成此小节")


class SectionDetail(BaseModel):
    """小节详情 - 包含内容"""
    id: int
    chapter_id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    order_index: int
    estimated_minutes: int = Field(default=15)
    learning_objectives: Optional[List[str]] = None
    is_completed: bool = Field(default=False)
    last_position: str = Field(default="content", description="最后学习位置")


class SectionListResponse(BaseModel):
    """小节列表响应"""
    sections: List[SectionSummary]
    total: int


class SectionDetailResponse(BaseModel):
    """小节详情响应"""
    section: SectionDetail


class SaveSectionProgressRequest(BaseModel):
    """保存小节学习进度请求"""
    position: str = Field(..., description="当前位置: content 或 quiz")
    is_completed: bool = Field(default=False, description="是否标记为完成")


class SectionProgressResponse(BaseModel):
    """小节进度响应"""
    section_id: int
    is_completed: bool
    last_position: str
    completed_at: Optional[datetime] = None


class CurrentPositionResponse(BaseModel):
    """当前学习位置响应"""
    course_id: int
    chapter_id: int
    section_id: int
    position: str = Field(description="当前位置: content 或 quiz")
    chapter_title: Optional[str] = None
    section_title: Optional[str] = None
