from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SolutionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")
    problem_link: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_announcement: bool = Field(default=False)


class SolutionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    problem_link: Optional[str] = None
    tags: Optional[List[str]] = None


class SolutionResponse(BaseModel):
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

    class Config:
        from_attributes = True


class SolutionListResponse(BaseModel):
    solutions: List[SolutionResponse]
    total: int
    page: int
    limit: int


class SolutionSummary(BaseModel):
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

    class Config:
        from_attributes = True
