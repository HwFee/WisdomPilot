"""Router for favorites endpoints - 完全依照 WrongQuestion 格式"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.favorites import (
    FavoriteCountResponse,
    FavoriteCreate,
    FavoriteFolderCreate,
    FavoriteFolderResponse,
    FavoriteFoldersListResponse,
    FavoriteListResponse,
    FavoriteResponse,
    FavoriteUpdate,
)
from app.utils.deps import get_current_active_user

logger = logging.getLogger(__name__)

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

    与错题本完全一致的存储逻辑：
    - 如果有 exercise_key，用 exercise_key 去重
    - 如果没有 exercise_key，用 exercise_id 去重
    - 存储完整信息快照
    """
    logger.info(f"[API] 添加收藏请求: user_id={current_user.id}")
    logger.info(f"[API] 请求数据: exercise_key={request.exercise_key}, exercise_id={request.exercise_id}, course_id={request.course_id}")
    logger.info(f"[API] 请求数据: chapter_id={request.chapter_id}, exercise_type={request.exercise_type}, exercise_difficulty={request.exercise_difficulty}")
    logger.info(f"[API] 请求数据: knowledge_points={request.knowledge_points}")
    logger.info(f"[API] 请求数据: exercise_content={request.exercise_content}")

    # 检查是否已存在（与错题本一致的去重逻辑）
    existing = None
    if request.exercise_key:
        logger.info(f"[API] 使用 exercise_key 查询: {request.exercise_key}")
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.exercise_key == request.exercise_key,
            )
        )
        existing = result.scalar_one_or_none()
    elif request.exercise_id:
        logger.info(f"[API] 使用 exercise_id 查询: {request.exercise_id}")
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.exercise_id == request.exercise_id,
            )
        )
        existing = result.scalar_one_or_none()
    else:
        logger.warning(f"[API] 没有 exercise_key 和 exercise_id，无法去重")

    if existing:
        logger.info(f"[API] 收藏已存在: id={existing.id}")
        # 已存在：更新 note/folder 如果提供
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
        logger.info(f"[API] 收藏已存在，已更新: id={existing.id}")
        return existing

    # 创建新收藏（完全依照 WrongQuestion 的字段）
    logger.info(f"[API] 创建新收藏")
    favorite = Favorite(
        user_id=current_user.id,
        # 与错题本一致的字段
        exercise_key=request.exercise_key,
        exercise_id=request.exercise_id,
        course_id=request.course_id,
        chapter_id=request.chapter_id,
        knowledge_points=request.knowledge_points or [],
        exercise_content=request.exercise_content,
        exercise_type=request.exercise_type or "choice",
        exercise_difficulty=request.exercise_difficulty or 1,
        # 收藏夹特有
        folder=request.folder,
        note=request.note,
    )
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    logger.info(f"[API] 收藏添加成功: id={favorite.id}")
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

    与错题本完全一致：直接返回存储的信息，source_type/source_label/question_title 通过 property 计算
    """
    # 构建查询
    base_query = select(Favorite).where(Favorite.user_id == current_user.id)
    if folder:
        base_query = base_query.where(Favorite.folder == folder)

    # 获取总数
    count_query = select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    if folder:
        count_query = count_query.where(Favorite.folder == folder)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # 获取收藏列表
    result = await db.execute(
        base_query.order_by(Favorite.created_at.desc()).limit(limit).offset(offset)
    )
    favorites = list(result.scalars().all())

    # 直接使用 FavoriteResponse 的 model_validate，property 会自动计算
    favorite_responses = [FavoriteResponse.model_validate(fav) for fav in favorites]

    return FavoriteListResponse(favorites=favorite_responses, total=total)


@router.get("/count", response_model=FavoriteCountResponse)
async def get_favorites_count(
    db: db_dependency,
    current_user: auth_dependency,
    folder: Optional[str] = Query(default=None, description="Filter by folder name"),
):
    """Get favorites count"""
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
        select(Favorite.folder, func.count(Favorite.id).label("count"))
        .where(Favorite.user_id == current_user.id)
        .where(Favorite.folder.isnot(None))
        .group_by(Favorite.folder)
        .order_by(func.count(Favorite.id).desc())
    )
    rows = result.all()

    folders = [FavoriteFolderResponse(name=row.folder, count=row.count) for row in rows]

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


@router.get("/check")
async def check_favorite(
    db: db_dependency,
    current_user: auth_dependency,
    exercise_key: Optional[str] = Query(default=None, description="Exercise key to check"),
    exercise_id: Optional[int] = Query(default=None, description="Exercise ID to check"),
):
    """Check whether the current user has favorited a specific exercise.

    与错题本一致：支持 exercise_key 或 exercise_id 查询

    Returns:
        is_favorited: True if a matching favorite record exists.
        favorite_id:  The UUID string of that record, or null when not found.
    """
    favorite = None
    if exercise_key:
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.exercise_key == exercise_key,
            )
        )
        favorite = result.scalar_one_or_none()
    elif exercise_id:
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.exercise_id == exercise_id,
            )
        )
        favorite = result.scalar_one_or_none()

    return {
        "is_favorited": favorite is not None,
        "favorite_id": str(favorite.id) if favorite is not None else None,
    }


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
