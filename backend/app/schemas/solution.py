"""Solution schemas - 题解相关的请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SolutionCreate(BaseModel):
    """创建题解请求"""

    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(default="", description="内容")
    problem_link: Optional[str] = Field(None, description="题目链接")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    is_announcement: bool = Field(default=False, description="是否为公告")


class SolutionUpdate(BaseModel):
    """更新题解请求"""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    content: Optional[str] = Field(None, description="内容")
    problem_link: Optional[str] = Field(None, description="题目链接")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class SolutionResponse(BaseModel):
    """题解响应"""

    id: int
    user_id: str
    username: str = ""
    title: str
    content: str
    problem_link: Optional[str] = None
    tags: List[str] = []
    is_pinned: bool = False
    is_announcement: bool = False
    view_count: int = 0
    like_count: int = 0
    created_at: datetime
    updated_at: datetime
    hot_score: float = 0.0

    model_config = {"from_attributes": True}


class SolutionListResponse(BaseModel):
    """题解列表响应"""

    solutions: List[SolutionResponse]
    total: int
    page: int
    limit: int


class SolutionSummary(BaseModel):
    """题解摘要（用于列表展示）"""

    id: int
    user_id: str
    username: str = ""
    title: str
    is_pinned: bool = False
    is_announcement: bool = False
    view_count: int = 0
    like_count: int = 0
    created_at: datetime
    hot_score: float = 0.0

    model_config = {"from_attributes": True}
