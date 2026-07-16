"""Router for note tags endpoints"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.models.note import NoteTag
import logging

from app.schemas.note import (
    NoteTagCreate,
    NoteTagUpdate,
    NoteTagResponse,
    NoteTagListResponse,
)

router = APIRouter(prefix="/api/note-tags", tags=["note_tags"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


@router.post("", response_model=NoteTagResponse)
async def create_tag(
    request: NoteTagCreate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Create a new note tag"""
    # Check if tag with same name already exists
    result = await db.execute(
        select(NoteTag).where(
            NoteTag.user_id == current_user.id,
            NoteTag.name == request.name,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")

    tag = NoteTag(
        user_id=current_user.id,
        name=request.name,
        color=request.color,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("", response_model=NoteTagListResponse)
async def get_tags(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get all tags for current user"""
    result = await db.execute(
        select(NoteTag).where(NoteTag.user_id == current_user.id).order_by(NoteTag.name)
    )
    tags = list(result.scalars().all())

    return NoteTagListResponse(
        tags=[NoteTagResponse.model_validate(t) for t in tags], total=len(tags)
    )


@router.put("/{tag_id}", response_model=NoteTagResponse)
async def update_tag(
    tag_id: str,
    request: NoteTagUpdate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Update a tag"""
    result = await db.execute(
        select(NoteTag).where(
            NoteTag.id == tag_id,
            NoteTag.user_id == current_user.id,
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if request.name is not None:
        # Check if another tag with same name exists
        existing_result = await db.execute(
            select(NoteTag).where(
                NoteTag.user_id == current_user.id,
                NoteTag.name == request.name,
                NoteTag.id != tag_id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=400, detail="Tag with this name already exists"
            )
        tag.name = request.name

    if request.color is not None:
        tag.color = request.color

    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: str,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Delete a tag"""
    result = await db.execute(
        select(NoteTag).where(
            NoteTag.id == tag_id,
            NoteTag.user_id == current_user.id,
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.commit()
    return {"success": True}


logger = logging.getLogger(__name__)
