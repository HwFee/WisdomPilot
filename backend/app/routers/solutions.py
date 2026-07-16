"""Solutions router - 题解广场API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, cast

from app.database import get_db
from app.schemas.solution import (
    SolutionCreate,
    SolutionUpdate,
    SolutionResponse,
    SolutionListResponse,
    SolutionSummary,
)
from app.services import solution_service
from app.utils.deps import get_current_user, get_current_admin_user
from app.models.user import User
import logging

router = APIRouter(prefix="/api/solutions", tags=["题解广场"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=SolutionResponse)
async def create_solution(
    solution_data: SolutionCreate,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    """创建新题解"""
    # 只有管理员可以发布公告
    if solution_data.is_announcement and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以发布公告")
    solution = await solution_service.create_solution(
        db, solution_data, current_user.id
    )
    return await solution_service.get_solution_with_username(db, solution)


@router.get("", response_model=SolutionListResponse)
async def get_solutions(
    db: db_dependency,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query("hot", pattern="^(hot|new|pinned)$", description="排序方式"),
):
    """获取题解列表"""
    solutions, total = await solution_service.get_solutions(db, page, limit, sort)
    # 使用批量查询优化，避免 N+1 问题
    solution_list = await solution_service.get_solutions_with_usernames(db, solutions)
    return {
        "solutions": solution_list,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/summary", response_model=list[SolutionSummary])
async def get_solution_summary(
    db: db_dependency,
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
):
    """获取题解摘要（用于Dashboard展示，需要登录）"""
    solutions, _ = await solution_service.get_solutions(
        db, page=1, limit=limit, sort="hot"
    )
    # 使用批量查询优化
    return await solution_service.get_solutions_with_usernames(db, solutions)


@router.get("/{solution_id}", response_model=SolutionResponse)
async def get_solution(
    solution_id: int,
    db: db_dependency,
):
    """获取单个题解详情"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    # 增加浏览数
    await solution_service.increment_view(db, solution)
    return await solution_service.get_solution_with_username(db, solution)


@router.put("/{solution_id}", response_model=SolutionResponse)
async def update_solution(
    solution_id: int,
    update_data: SolutionUpdate,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    """更新题解（仅作者可操作）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    if cast(bool, solution.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="无权修改此题解")
    updated = await solution_service.update_solution(db, solution, update_data)
    return await solution_service.get_solution_with_username(db, updated)


@router.delete("/{solution_id}")
async def delete_solution(
    solution_id: int,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    """删除题解（作者或管理员可操作）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    # 作者或管理员可以删除
    if cast(bool, solution.user_id != current_user.id and not current_user.is_admin):
        raise HTTPException(status_code=403, detail="无权删除此题解")
    await solution_service.delete_solution(db, solution)
    return {"message": "删除成功"}


@router.post("/{solution_id}/like", response_model=SolutionResponse)
async def toggle_like(
    solution_id: int,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    """点赞/取消点赞（每人只能点赞一次）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    updated = await solution_service.toggle_like(db, solution, current_user.id)
    return await solution_service.get_solution_with_username(db, updated)


@router.post("/{solution_id}/pin", response_model=SolutionResponse)
async def toggle_pin(
    solution_id: int,
    db: db_dependency,
    current_user: User = Depends(get_current_admin_user),
):
    """置顶/取消置顶（仅管理员可操作）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    updated = await solution_service.toggle_pin(db, solution)
    return await solution_service.get_solution_with_username(db, updated)


logger = logging.getLogger(__name__)
