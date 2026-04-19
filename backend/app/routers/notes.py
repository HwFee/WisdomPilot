"""Router for notes endpoints"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.models.note import Note
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteFromQuestion,
    NoteResponse,
    NoteListResponse,
    NoteCountResponse,
    NoteSearchResponse,
    NoteExportRequest,
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
        tags=request.tags,
        knowledge_points=request.knowledge_points,
        source=request.source,
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
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get user's notes list, optionally filtered by chapter or tags"""
    query = select(Note).where(Note.user_id == current_user.id)
    count_query = select(func.count(Note.id)).where(Note.user_id == current_user.id)

    if chapter_id is not None:
        query = query.where(Note.chapter_id == chapter_id)
        count_query = count_query.where(Note.chapter_id == chapter_id)

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            # Filter notes that have any of the specified tags
            for tag in tag_list:
                query = query.where(Note.tags.contains(tag))
                count_query = count_query.where(Note.tags.contains(tag))

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get notes
    result = await db.execute(
        query.order_by(Note.updated_at.desc()).limit(limit).offset(offset)
    )
    notes = list(result.scalars().all())

    return NoteListResponse(notes=notes, total=total)


@router.get("/search", response_model=NoteSearchResponse)
async def search_notes(
    db: db_dependency,
    current_user: auth_dependency,
    q: str = Query(..., min_length=1, description="Search query"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    chapter_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Search notes by content, title, or knowledge points"""
    query = select(Note).where(
        Note.user_id == current_user.id,
        or_(
            Note.title.ilike(f"%{q}%"),
            Note.content.ilike(f"%{q}%"),
            Note.knowledge_points.ilike(f"%{q}%"),
        )
    )
    count_query = select(func.count(Note.id)).where(
        Note.user_id == current_user.id,
        or_(
            Note.title.ilike(f"%{q}%"),
            Note.content.ilike(f"%{q}%"),
            Note.knowledge_points.ilike(f"%{q}%"),
        )
    )

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            query = query.where(Note.tags.contains(tag))
            count_query = count_query.where(Note.tags.contains(tag))

    if chapter_id is not None:
        query = query.where(Note.chapter_id == chapter_id)
        count_query = count_query.where(Note.chapter_id == chapter_id)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get notes
    result = await db.execute(
        query.order_by(Note.updated_at.desc()).limit(limit)
    )
    notes = list(result.scalars().all())

    return NoteSearchResponse(notes=notes, total=total, query=q)


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


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get a specific note"""
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


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
    if request.tags is not None:
        note.tags = request.tags
    if request.knowledge_points is not None:
        note.knowledge_points = request.knowledge_points

    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}", response_model=dict)
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
    return {"success": True, "deleted": True}


@router.post("/from-question", response_model=NoteResponse)
async def create_note_from_question(
    request: NoteFromQuestion,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Create a note from a question or AI answer content"""
    # Build content from question/AI answer if provided
    content = request.content
    if request.question_content:
        content = f"## 题目\n\n{request.question_content}\n\n---\n\n## 我的笔记\n\n{content}"
    if request.ai_answer_content:
        content = f"{content}\n\n## AI回答\n\n{request.ai_answer_content}"

    note = Note(
        user_id=current_user.id,
        title=request.title,
        content=content,
        exercise_id=request.exercise_id,
        chapter_id=request.chapter_id,
        subsection_index=request.subsection_index,
        knowledge_points=request.knowledge_points,
        source=request.source,
        tags=[],  # User can add tags later
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/export/{note_id}")
async def export_note(
    note_id: str,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Export a single note as Markdown"""
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Build markdown content
    md_content = f"# {note.title or 'Untitled Note'}\n\n"
    if note.tags:
        md_content += f"**Tags:** {', '.join(note.tags)}\n\n"
    if note.knowledge_points:
        md_content += f"**知识点:** {', '.join(note.knowledge_points)}\n\n"
    md_content += f"---\n\n{note.content}\n\n"
    md_content += f"\n\n---\n*Created: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}*"

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=note_{note_id}.md"
        }
    )


@router.post("/export")
async def export_notes(
    request: NoteExportRequest,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Export multiple notes as Markdown or JSON"""
    result = await db.execute(
        select(Note).where(
            Note.id.in_(request.note_ids),
            Note.user_id == current_user.id,
        )
    )
    notes = list(result.scalars().all())

    if not notes:
        raise HTTPException(status_code=404, detail="No notes found")

    if request.format == "markdown":
        # Combine all notes into one markdown file
        md_content = "# My Notes\n\n"
        for i, note in enumerate(notes, 1):
            md_content += f"## {i}. {note.title or 'Untitled Note'}\n\n"
            if note.tags:
                md_content += f"**Tags:** {', '.join(note.tags)}\n\n"
            if note.knowledge_points:
                md_content += f"**知识点:** {', '.join(note.knowledge_points)}\n\n"
            md_content += f"---\n\n{note.content}\n\n"
            md_content += f"*Created: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "attachment; filename=notes_export.md"
            }
        )
    else:
        # JSON format
        import json
        notes_data = [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "knowledge_points": note.knowledge_points,
                "source": note.source,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
            }
            for note in notes
        ]
        return Response(
            content=json.dumps(notes_data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=notes_export.json"
            }
        )
