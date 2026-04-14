"""Router for favorites endpoints"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.models.favorite import Favorite
from app.schemas.favorites import (
    FavoriteCreate,
    FavoriteResponse,
    FavoriteListResponse,
    FavoriteCountResponse,
)

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


@router.post("", response_model=FavoriteResponse)
async def add_favorite(
    request: FavoriteCreate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Add an exercise to favorites"""
    # Check if already exists
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.exercise_id == request.exercise_id,
            Favorite.chapter_id == request.chapter_id,
            Favorite.subsection_index == request.subsection_index,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update note if provided
        if request.note is not None:
            existing.note = request.note
            await db.commit()
            await db.refresh(existing)
        return existing

    # Create new favorite
    favorite = Favorite(
        user_id=current_user.id,
        exercise_id=request.exercise_id,
        chapter_id=request.chapter_id,
        subsection_index=request.subsection_index,
        note=request.note,
    )
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


@router.get("", response_model=FavoriteListResponse)
async def get_favorites(
    db: db_dependency,
    current_user: auth_dependency,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get user's favorites list"""
    # Get total count
    count_result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Get favorites
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    favorites = list(result.scalars().all())

    return FavoriteListResponse(favorites=favorites, total=total)


@router.get("/count", response_model=FavoriteCountResponse)
async def get_favorites_count(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get favorites count"""
    result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    )
    count = result.scalar() or 0
    return FavoriteCountResponse(count=count)


@router.delete("/{favorite_id}")
async def remove_favorite(
    favorite_id: str,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Remove a favorite"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.id == favorite_id,
            Favorite.user_id == current_user.id,
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.delete(favorite)
    await db.commit()
    return {"success": True}
