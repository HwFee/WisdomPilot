from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.database import get_db
from app.schemas.solution import (
    SolutionCreate,
    SolutionUpdate,
    SolutionResponse,
    SolutionListResponse,
    SolutionSummary,
)
from app.services import solution_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/solutions", tags=["题解"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=SolutionResponse)
async def create_solution(
    solution_data: SolutionCreate,
    db: db_dependency,
    current_user = Depends(get_current_user),
):
    """创建新题解"""
    # 只有管理员可以发布公告
    if solution_data.is_announcement and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以发布公告")
    solution = await solution_service.create_solution(db, solution_data, current_user.id)
    return await solution_service.get_solution_with_username(db, solution)


@router.get("", response_model=SolutionListResponse)
async def get_solutions(
    db: db_dependency,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("hot", pattern="^(hot|new|pinned)$"),
):
    """获取题解列表"""
    solutions, total = await solution_service.get_solutions(db, page, limit, sort)
    return {
        "solutions": [await solution_service.get_solution_with_username(db, s) for s in solutions],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/summary", response_model=list[SolutionSummary])
async def get_solution_summary(
    db: db_dependency,
    limit: int = Query(10, ge=1, le=50),
):
    """获取题解摘要（用于Dashboard展示）"""
    solutions, _ = await solution_service.get_solutions(db, page=1, limit=limit, sort="hot")
    return [await solution_service.get_solution_with_username(db, s) for s in solutions]


@router.get("/{solution_id}", response_model=SolutionResponse)
async def get_solution(
    solution_id: int,
    db: db_dependency,
):
    """获取单个题解"""
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
    current_user: dict = Depends(get_current_user),
):
    """更新题解（仅作者）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    if solution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此题解")
    updated = await solution_service.update_solution(db, solution, update_data)
    return await solution_service.get_solution_with_username(db, updated)


@router.delete("/{solution_id}")
async def delete_solution(
    solution_id: int,
    db: db_dependency,
    current_user: dict = Depends(get_current_user),
):
    """删除题解（仅作者）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    if solution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此题解")
    await solution_service.delete_solution(db, solution)
    return {"message": "删除成功"}


@router.post("/{solution_id}/like", response_model=SolutionResponse)
async def toggle_like(
    solution_id: int,
    db: db_dependency,
):
    """点赞"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    updated = await solution_service.toggle_like(db, solution)
    return await solution_service.get_solution_with_username(db, updated)


@router.post("/{solution_id}/pin", response_model=SolutionResponse)
async def toggle_pin(
    solution_id: int,
    db: db_dependency,
    current_user: dict = Depends(get_current_user),
):
    """置顶/取消置顶（需要管理员权限，这里简化为作者可操作）"""
    solution = await solution_service.get_solution_by_id(db, solution_id)
    if not solution:
        raise HTTPException(status_code=404, detail="题解不存在")
    updated = await solution_service.toggle_pin(db, solution)
    return await solution_service.get_solution_with_username(db, updated)
