"""Schemas for favorites and notes"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ========================================
# Favorite Schemas
# ========================================

class FavoriteCreate(BaseModel):
    """Schema for creating a favorite"""
    exercise_id: int
    chapter_id: Optional[int] = None
    subsection_index: int = 0
    challenge_session_id: Optional[str] = None
    folder: Optional[str] = None
    note: Optional[str] = None


class FavoriteUpdate(BaseModel):
    """Schema for updating a favorite"""
    folder: Optional[str] = None
    note: Optional[str] = None


class FavoriteResponse(BaseModel):
    """Schema for favorite response"""
    id: str
    user_id: str
    exercise_id: int
    chapter_id: Optional[int] = None
    subsection_index: int
    challenge_session_id: Optional[str] = None
    folder: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteListResponse(BaseModel):
    """Schema for favorites list response"""
    favorites: list[FavoriteResponse]
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
    folders: list[FavoriteFolderResponse]


# ========================================
# Note Schemas
# ========================================

class NoteCreate(BaseModel):
    """Schema for creating a note"""
    title: Optional[str] = None
    content: str
    exercise_id: Optional[int] = None
    chapter_id: Optional[int] = None
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
    chapter_id: Optional[int] = None
    subsection_index: int
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
