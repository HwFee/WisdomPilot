"""Router for favorites endpoints"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.models.favorite import Favorite
from app.schemas.favorites import (
    FavoriteCreate,
    FavoriteUpdate,
    FavoriteResponse,
    FavoriteListResponse,
    FavoriteCountResponse,
    FavoriteFolderCreate,
    FavoriteFolderResponse,
    FavoriteFoldersListResponse,
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
    """Add an exercise to favorites

    Supports:
    - 精进之路收藏: provide chapter_id
    - 挑战之路收藏: provide challenge_session_id
    """
    # Build query conditions based on provided fields
    conditions = [
        Favorite.user_id == current_user.id,
        Favorite.exercise_id == request.exercise_id,
    ]

    if request.chapter_id is not None:
        conditions.append(Favorite.chapter_id == request.chapter_id)
        conditions.append(Favorite.subsection_index == request.subsection_index)
    else:
        conditions.append(Favorite.chapter_id.is_(None))

    if request.challenge_session_id is not None:
        conditions.append(Favorite.challenge_session_id == request.challenge_session_id)
    else:
        conditions.append(Favorite.challenge_session_id.is_(None))

    result = await db.execute(select(Favorite).where(*conditions))
    existing = result.scalar_one_or_none()

    if existing:
        # Update note/folder if provided
        updated = False
        if request.note is not None:
            existing.note = request.note
            updated = True
        if request.folder is not None:
            existing.folder = request.folder
            updated = True
        if updated:
            await db.commit()
            await db.refresh(existing)
        return existing

    # Create new favorite
    favorite = Favorite(
        user_id=current_user.id,
        exercise_id=request.exercise_id,
        chapter_id=request.chapter_id,
        subsection_index=request.subsection_index,
        challenge_session_id=request.challenge_session_id,
        folder=request.folder,
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
    folder: Optional[str] = Query(default=None, description="Filter by folder name"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get user's favorites list

    Args:
        folder: Optional folder name to filter by
    """
    # Build base query
    base_query = select(Favorite).where(Favorite.user_id == current_user.id)

    if folder:
        base_query = base_query.where(Favorite.folder == folder)

    # Get total count
    count_query = select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    if folder:
        count_query = count_query.where(Favorite.folder == folder)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get favorites
    result = await db.execute(
        base_query
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
    folder: Optional[str] = Query(default=None, description="Filter by folder name"),
):
    """Get favorites count

    Args:
        folder: Optional folder name to filter by
    """
    query = select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    if folder:
        query = query.where(Favorite.folder == folder)
    result = await db.execute(query)
    count = result.scalar() or 0
    return FavoriteCountResponse(count=count)


@router.get("/folders", response_model=FavoriteFoldersListResponse)
async def get_favorite_folders(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get user's favorite folders with counts"""
    # Get distinct folders with counts
    result = await db.execute(
        select(
            Favorite.folder,
            func.count(Favorite.id).label('count')
        )
        .where(Favorite.user_id == current_user.id)
        .where(Favorite.folder.isnot(None))
        .group_by(Favorite.folder)
        .order_by(func.count(Favorite.id).desc())
    )
    rows = result.all()

    folders = [
        FavoriteFolderResponse(name=row.folder, count=row.count)
        for row in rows
    ]

    # Add "默认" folder for ungrouped favorites
    default_count_result = await db.execute(
        select(func.count(Favorite.id))
        .where(Favorite.user_id == current_user.id)
        .where(Favorite.folder.is_(None))
    )
    default_count = default_count_result.scalar() or 0
    if default_count > 0:
        folders.append(FavoriteFolderResponse(name="默认", count=default_count))

    return FavoriteFoldersListResponse(folders=folders)


@router.post("/folders", response_model=FavoriteFolderResponse)
async def create_folder(
    request: FavoriteFolderCreate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Create a new favorite folder (just returns the name, folders are created on-demand)"""
    return FavoriteFolderResponse(name=request.name, count=0)


@router.patch("/{favorite_id}", response_model=FavoriteResponse)
async def update_favorite(
    favorite_id: str,
    request: FavoriteUpdate,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Update a favorite's folder or note"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.id == favorite_id,
            Favorite.user_id == current_user.id,
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    if request.folder is not None:
        favorite.folder = request.folder
    if request.note is not None:
        favorite.note = request.note

    await db.commit()
    await db.refresh(favorite)
    return favorite


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


@router.post("/batch-delete")
async def batch_remove_favorites(
    favorite_ids: list[str],
    db: db_dependency,
    current_user: auth_dependency,
):
    """Remove multiple favorites at once"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.id.in_(favorite_ids),
            Favorite.user_id == current_user.id,
        )
    )
    favorites = result.scalars().all()

    for favorite in favorites:
        await db.delete(favorite)

    await db.commit()
    return {"success": True, "deleted_count": len(favorites)}
