from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.utils.deps import get_current_active_user
from app.services.admin import AdminService
import logging

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin privileges"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all users (admin only) with pagination."""
    service = AdminService(db)
    users = await service.list_users()
    page = users[skip : skip + limit]
    return [UserResponse.model_validate(u) for u in page]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete a user (admin only)."""
    service = AdminService(db)
    try:
        success = await service.delete_user(user_id)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Cannot delete user due to integrity constraints")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Internal server error deleting user")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/users/online", response_model=list[UserResponse])
async def list_online_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List currently online users (admin only)"""
    service = AdminService(db)
    users = await service.get_online_users()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/users/{user_id}/quota")
async def get_user_quota(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get user's AI quota status (admin only)"""
    from app.services.quota import quota_service

    user = await quota_service.get_or_create_user_quota(user_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return await quota_service.get_quota(user, db)


@router.put("/users/{user_id}/quota")
async def set_user_quota(
    user_id: str,
    amount: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Set user's AI quota to a specific amount (admin only)"""
    from app.services.quota import quota_service

    user = await quota_service.get_or_create_user_quota(user_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await quota_service.set_quota(user, db, amount)
    return {"message": "Quota updated", "quota": amount}


@router.post("/users/{user_id}/quota/reset")
async def reset_user_quota(
    user_id: str,
    amount: int = 100,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Reset user's AI quota to default (admin only)"""
    from app.services.quota import quota_service

    user = await quota_service.get_or_create_user_quota(user_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await quota_service.reset_quota(user, db, amount)
    return {"message": "Quota reset", "quota": amount}


logger = logging.getLogger(__name__)