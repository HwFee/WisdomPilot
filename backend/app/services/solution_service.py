from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.solution import Solution
from app.models.solution_like import SolutionLike
from app.models.user import User
from app.schemas.solution import SolutionCreate, SolutionUpdate


def calculate_hot_score(solution: Solution) -> float:
    """计算热度分数"""
    now = datetime.now(solution.created_at.tzinfo) if solution.created_at.tzinfo else datetime.utcnow()
    age = now - solution.created_at

    # 时间衰减奖励
    recency_bonus = 0.0
    if age < timedelta(hours=1):
        recency_bonus = 10
    elif age < timedelta(days=1):
        recency_bonus = 5
    elif age < timedelta(days=7):
        recency_bonus = 2
    elif age < timedelta(days=30):
        recency_bonus = 1

    return solution.like_count * 2 + solution.view_count * 0.1 + recency_bonus


async def get_solution_with_username(db: AsyncSession, solution: Solution) -> dict:
    """获取题解并添加用户名"""
    result = await db.execute(select(User).where(User.id == solution.user_id))
    user = result.scalar_one_or_none()
    return {
        "id": solution.id,
        "user_id": solution.user_id,
        "username": user.username if user else "未知用户",
        "title": solution.title,
        "content": solution.content,
        "problem_link": solution.problem_link,
        "tags": solution.tags or [],
        "is_pinned": solution.is_pinned,
        "is_announcement": solution.is_announcement,
        "view_count": solution.view_count,
        "like_count": solution.like_count,
        "created_at": solution.created_at,
        "updated_at": solution.updated_at,
        "hot_score": calculate_hot_score(solution),
    }


async def create_solution(db: AsyncSession, solution_data: SolutionCreate, user_id: str) -> Solution:
    """创建题解"""
    db_solution = Solution(
        user_id=user_id,
        title=solution_data.title,
        content=solution_data.content or "",
        problem_link=solution_data.problem_link,
        tags=solution_data.tags or [],
        is_announcement=solution_data.is_announcement,
    )
    db.add(db_solution)
    await db.commit()
    await db.refresh(db_solution)
    return db_solution


async def get_solutions(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    sort: str = "hot"
) -> tuple[List[Solution], int]:
    """获取题解列表，支持排序"""
    # 获取总数
    count_result = await db.execute(select(func.count()).select_from(Solution))
    total = count_result.scalar_one()

    # 构建查询
    query = select(Solution)

    if sort == "new":
        query = query.order_by(desc(Solution.created_at))
    elif sort == "pinned":
        query = query.where(Solution.is_pinned == True).order_by(desc(Solution.created_at))
    else:  # hot
        # 按热度排序：置顶优先，然后按热度分数
        query = query.order_by(desc(Solution.is_pinned), desc(Solution.like_count), desc(Solution.view_count), desc(Solution.created_at))

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    solutions = result.scalars().all()

    return list(solutions), total


async def get_solution_by_id(db: AsyncSession, solution_id: int) -> Optional[Solution]:
    """获取单个题解"""
    result = await db.execute(select(Solution).where(Solution.id == solution_id))
    return result.scalar_one_or_none()


async def update_solution(db: AsyncSession, solution: Solution, update_data: SolutionUpdate) -> Solution:
    """更新题解"""
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(solution, key, value)
    await db.commit()
    await db.refresh(solution)
    return solution


async def delete_solution(db: AsyncSession, solution: Solution) -> None:
    """删除题解"""
    await db.delete(solution)
    await db.commit()


async def toggle_like(db: AsyncSession, solution: Solution, user_id: str) -> Solution:
    """点赞/取消点赞（每人只能点赞一次）"""
    # 先尝试删除（如果存在的话）
    existing = await db.execute(
        select(SolutionLike).where(
            SolutionLike.user_id == user_id,
            SolutionLike.solution_id == solution.id
        )
    )
    existing_like = existing.scalar_one_or_none()

    if existing_like:
        # 已点赞，取消点赞
        await db.delete(existing_like)
        solution.like_count = max(0, solution.like_count - 1)
    else:
        # 未点赞，先确保 solution.like_count 已同步（处理并发情况）
        actual_count = await db.execute(
            select(func.count()).select_from(SolutionLike).where(SolutionLike.solution_id == solution.id)
        )
        solution.like_count = actual_count.scalar() + 1
        new_like = SolutionLike(user_id=user_id, solution_id=solution.id)
        db.add(new_like)

    await db.commit()
    await db.refresh(solution)
    return solution


async def toggle_pin(db: AsyncSession, solution: Solution) -> Solution:
    """切换置顶状态"""
    solution.is_pinned = not solution.is_pinned
    await db.commit()
    await db.refresh(solution)
    return solution


async def increment_view(db: AsyncSession, solution: Solution) -> Solution:
    """增加浏览数"""
    solution.view_count += 1
    await db.commit()
    await db.refresh(solution)
    return solution
