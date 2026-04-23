"""Chapter API Router - Direct chapter access"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.chapter import Chapter
from app.schemas.course import ChapterDetailResponse, ChapterDetail, ExerciseSummary
import logging

router = APIRouter(prefix="/api/chapters", tags=["chapters"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.get("/{chapter_id}", response_model=ChapterDetailResponse)
async def get_chapter_by_id(chapter_id: int, db: db_dependency):
    """
    Get chapter details by chapter ID directly.

    Returns chapter info with embedded exercise list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Chapter)
        .where(Chapter.id == chapter_id)
        .options(selectinload(Chapter.exercises))
    )

    result = await db.execute(query)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    exercises = [
        ExerciseSummary(
            id=ex.id,
            chapter_id=ex.chapter_id,
            source=ex.source,
            source_id=ex.source_id,
            type=ex.type,
            difficulty=ex.difficulty,
            content=ex.content,
            hints=ex.hints,
        )
        for ex in chapter.exercises
    ]

    chapter_detail = ChapterDetail(
        id=chapter.id,
        course_id=chapter.course_id,
        title=chapter.title,
        description=chapter.description,
        content=chapter.content,
        order_index=chapter.order_index,
        learning_objectives=chapter.learning_objectives,
        difficulty_tags=chapter.difficulty_tags,
        skill_tags=chapter.skill_tags,
        estimated_minutes=chapter.estimated_minutes,
        is_active=chapter.is_active,
    )

    return ChapterDetailResponse(chapter=chapter_detail, exercises=exercises)


logger = logging.getLogger(__name__)