"""Section schemas - 小节相关的请求/响应模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class KnowledgePointDetail(BaseModel):
    """知识点详情"""
    id: int
    order_index: int = Field(description="显示顺序")
    name: str = Field(description="知识点名称")
    content: Optional[str] = Field(default=None, description="知识点讲解内容（Markdown格式）")
    summary: Optional[str] = Field(default=None, description="知识点简要总结")
    code_example: Optional[str] = Field(default=None, description="代码示例")
    code_language: str = Field(default="c", description="代码语言")
    code_explanation: Optional[str] = Field(default=None, description="代码示例解释")
    difficulty: int = Field(default=1, description="难度等级 1-5")
    importance: int = Field(default=1, description="重要程度 1-5")
    tips: Optional[List[str]] = Field(default=None, description="学习提示列表")
    common_mistakes: Optional[List[str]] = Field(default=None, description="常见错误列表")


class SectionSummary(BaseModel):
    """小节摘要 - 用于列表显示"""
    id: int
    chapter_id: int
    title: str
    description: Optional[str] = None
    order_index: int
    estimated_minutes: int = Field(default=15, description="预计学习时间（分钟）")
    is_completed: bool = Field(default=False, description="用户是否已完成此小节")
    mastery_score: Optional[float] = Field(default=None, description="BKT 聚合掌握度 0-100")


class SectionDetail(BaseModel):
    """小节详情 - 包含内容和知识点列表"""
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
    # 新增：知识点列表
    knowledge_points: List[KnowledgePointDetail] = Field(default_factory=list, description="知识点列表")


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
