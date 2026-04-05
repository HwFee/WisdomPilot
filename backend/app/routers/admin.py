from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.utils.deps import get_current_active_user
from app.services.admin import AdminService

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
    skip: int = 0,
    limit: int = 20,
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
