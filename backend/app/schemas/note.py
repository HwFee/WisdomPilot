"""Schemas for notes"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


# ========================================
# Note Schemas
# ========================================

class NoteCreate(BaseModel):
    """Schema for creating a note"""
    title: Optional[str] = None
    content: str
    course_id: Optional[int] = None
    chapter_id: Optional[int] = None
    section_id: Optional[int] = None
    exercise_id: Optional[int] = None
    subsection_index: int = 0
    tags: List[str] = Field(default_factory=list)
    knowledge_points: List[str] = Field(default_factory=list)
    source: Literal['manual', 'ai_answer', 'question'] = "manual"


class NoteUpdate(BaseModel):
    """Schema for updating a note"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    knowledge_points: Optional[List[str]] = None


class NoteFromQuestion(BaseModel):
    """Schema for creating a note from question or AI answer"""
    title: Optional[str] = None
    content: str
    course_id: Optional[int] = None
    chapter_id: Optional[int] = None
    section_id: Optional[int] = None
    exercise_id: Optional[int] = None
    subsection_index: int = 0
    knowledge_points: List[str] = Field(default_factory=list)
    source: Literal['ai_answer', 'question'] = "question"
    question_content: Optional[str] = None
    ai_answer_content: Optional[str] = None


class NoteResponse(BaseModel):
    """Schema for note response"""
    id: str
    user_id: str
    title: Optional[str] = None
    content: str
    course_id: Optional[int] = None
    chapter_id: Optional[int] = None
    section_id: Optional[int] = None
    exercise_id: Optional[int] = None
    subsection_index: int
    tags: List[str] = Field(default_factory=list)
    knowledge_points: List[str] = Field(default_factory=list)
    source: Literal['manual', 'ai_answer', 'question']
    processing_status: Literal['pending', 'processing', 'completed'] = "completed"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Schema for notes list response"""
    notes: list[NoteResponse]
    total: int


class NoteCountResponse(BaseModel):
    """Schema for notes count response"""
    count: int


class NoteSearchResponse(BaseModel):
    """Schema for note search response"""
    notes: list[NoteResponse]
    total: int
    query: str


# ========================================
# Note Tag Schemas
# ========================================

class NoteTagCreate(BaseModel):
    """Schema for creating a note tag"""
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#6366f1", max_length=20)

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be a valid hex color (e.g., #6366f1)')
        return v


class NoteTagUpdate(BaseModel):
    """Schema for updating a note tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=20)


class NoteTagResponse(BaseModel):
    """Schema for note tag response"""
    id: str
    user_id: str
    name: str
    color: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteTagListResponse(BaseModel):
    """Schema for note tags list response"""
    tags: list[NoteTagResponse]
    total: int


# ========================================
# Note Export Schemas
# ========================================

class NoteExportRequest(BaseModel):
    """Schema for exporting notes"""
    note_ids: List[str] = Field(..., min_length=1)
    format: str = Field(default="markdown", pattern="^(markdown|json)$")
