"""Schemas for favorites - 完全依照 WrongQuestion 格式"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========================================
# Favorite Schemas - 依照 WrongQuestion
# ========================================

class FavoriteBase(BaseModel):
    """Base favorite schema - 与 WrongQuestionBase 一致"""
    exercise_id: Optional[int] = None
    exercise_key: Optional[str] = None
    course_id: int
    chapter_id: Optional[int] = None
    knowledge_points: List[str] = []
    exercise_type: str = "choice"
    exercise_difficulty: int = 1


class FavoriteCreate(BaseModel):
    """Schema for creating a favorite - 与 CollectWrongQuestionRequest 一致"""
    exercise_key: Optional[str] = Field(None, description="练习题标识")
    course_id: int = Field(..., description="课程ID")
    chapter_id: Optional[int] = Field(None, description="章节ID")
    exercise_id: Optional[int] = Field(None, description="原始练习题ID")
    exercise_content: Optional[dict] = Field(None, description="题目内容快照")
    exercise_type: Optional[str] = Field(None, description="题目类型")
    exercise_difficulty: Optional[int] = Field(None, description="题目难度")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")
    # 收藏夹特有
    folder: Optional[str] = None
    note: Optional[str] = None


class FavoriteUpdate(BaseModel):
    """Schema for updating a favorite"""
    folder: Optional[str] = None
    note: Optional[str] = None


class FavoriteResponse(BaseModel):
    """Schema for favorite response - 与 WrongQuestionResponse 一致"""
    id: str
    user_id: str
    # 与错题本一致的字段
    exercise_id: Optional[int] = None
    exercise_key: Optional[str] = None
    course_id: int
    chapter_id: Optional[int] = None
    knowledge_points: List[str] = []
    exercise_content: Optional[dict] = None
    exercise_type: str = "choice"
    exercise_difficulty: int = 1
    # 收藏夹特有
    folder: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @property
    def source_type(self) -> str:
        """题目来源类型: mastery(精进之路), arena(挑战之路), enhanced(强化测试)"""
        if not self.exercise_key:
            return "unknown"
        if self.exercise_key.startswith("mastery-"):
            return "mastery"
        elif self.exercise_key.startswith("arena-"):
            return "arena"
        elif self.exercise_key.startswith("enhanced-"):
            return "enhanced"
        return "unknown"

    @property
    def source_label(self) -> str:
        """题目来源中文标签"""
        labels = {
            "mastery": "精进之路",
            "arena": "挑战之路",
            "enhanced": "强化测试",
            "unknown": "未知来源"
        }
        return labels.get(self.source_type, "未知来源")

    @property
    def question_title(self) -> str:
        """题目标题/摘要"""
        if not self.exercise_content:
            type_labels = {
                "choice": "选择题",
                "programming": "编程题",
                "fill_blank": "填空题",
                "fill": "填空题",
                "output": "输出题",
            }
            return type_labels.get(self.exercise_type, f"{self.exercise_type}题")
        # 尝试从 content 中提取标题
        if "title" in self.exercise_content:
            return self.exercise_content["title"]
        if "text" in self.exercise_content:
            text = self.exercise_content["text"]
            # 截取前50个字符作为标题
            if len(text) > 50:
                return text[:50] + "..."
            return text
        type_labels = {
            "choice": "选择题",
            "programming": "编程题",
            "fill_blank": "填空题",
            "fill": "填空题",
            "output": "输出题",
        }
        return type_labels.get(self.exercise_type, f"{self.exercise_type}题")


class FavoriteListResponse(BaseModel):
    """Schema for favorites list response"""
    favorites: List[FavoriteResponse]
    total: int


class FavoriteCountResponse(BaseModel):
    """Schema for favorites count response"""
    count: int


# ========================================
# Favorite Folder Schemas
# ========================================

class FavoriteFolderCreate(BaseModel):
    """Schema for creating a favorite folder"""
    name: str = Field(..., min_length=1, max_length=50)


class FavoriteFolderResponse(BaseModel):
    """Schema for favorite folder response"""
    name: str
    count: int


class FavoriteFoldersListResponse(BaseModel):
    """Schema for favorite folders list response"""
    folders: List[FavoriteFolderResponse]


# ========================================
# Note Schemas
# ========================================

class NoteCreate(BaseModel):
    """Schema for creating a note"""
    title: Optional[str] = None
    content: str
    exercise_id: Optional[int] = None
    chapter_id: int = 0
    subsection_index: int = 0


class NoteUpdate(BaseModel):
    """Schema for updating a note"""
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(BaseModel):
    """Schema for note response"""
    id: str
    user_id: str
    title: Optional[str] = None
    content: str
    exercise_id: Optional[int] = None
    chapter_id: int
    subsection_index: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Schema for notes list response"""
    notes: List[NoteResponse]
    total: int


class NoteCountResponse(BaseModel):
    """Schema for notes count response"""
    count: int
