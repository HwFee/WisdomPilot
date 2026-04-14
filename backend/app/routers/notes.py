"""Router for notes endpoints"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.models.note import Note
from app.schemas.favorites import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    NoteCountResponse,
)

router = APIRouter(prefix="/api/notes", tags=["notes"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


@router.post("", response_model=NoteResponse)
async def create_note(
    request: NoteCreate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Create a new note"""
    note = Note(
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        exercise_id=request.exercise_id,
        chapter_id=request.chapter_id,
        subsection_index=request.subsection_index,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("", response_model=NoteListResponse)
async def get_notes(
    db: db_dependency,
    current_user: auth_dependency,
    chapter_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get user's notes list, optionally filtered by chapter"""
    # Build query
    query = select(Note).where(Note.user_id == current_user.id)
    count_query = select(func.count(Note.id)).where(Note.user_id == current_user.id)

    if chapter_id is not None:
        query = query.where(Note.chapter_id == chapter_id)
        count_query = count_query.where(Note.chapter_id == chapter_id)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get notes
    result = await db.execute(
        query.order_by(Note.updated_at.desc()).limit(limit).offset(offset)
    )
    notes = list(result.scalars().all())

    return NoteListResponse(notes=notes, total=total)


@router.get("/count", response_model=NoteCountResponse)
async def get_notes_count(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get notes count"""
    result = await db.execute(
        select(func.count(Note.id)).where(Note.user_id == current_user.id)
    )
    count = result.scalar() or 0
    return NoteCountResponse(count=count)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    request: NoteUpdate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Update a note"""
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if request.title is not None:
        note.title = request.title
    if request.content is not None:
        note.content = request.content

    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Delete a note"""
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await db.delete(note)
    await db.commit()
    return {"success": True}
