"""Solution service - 题解业务逻辑"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from app.models.solution import Solution
from app.models.solution_like import SolutionLike
from app.models.user import User
from app.schemas.solution import SolutionCreate, SolutionUpdate

logger = logging.getLogger(__name__)


def calculate_hot_score(solution: Solution) -> float:
    """
    计算热度分数

    算法：点赞数权重较高 + 浏览数权重较低 + 时间衰减奖励
    """
    try:
        if solution.created_at:
            if solution.created_at.tzinfo:
                now = datetime.now(solution.created_at.tzinfo)
            else:
                now = datetime.utcnow()
            age = now - solution.created_at
        else:
            age = timedelta(days=365)

        # 时间衰减奖励
        recency_bonus = 0.0
        if age < timedelta(hours=1):
            recency_bonus = 10.0
        elif age < timedelta(days=1):
            recency_bonus = 5.0
        elif age < timedelta(days=7):
            recency_bonus = 2.0
        elif age < timedelta(days=30):
            recency_bonus = 1.0

        return solution.like_count * 2 + solution.view_count * 0.1 + recency_bonus
    except Exception as e:
        logger.error(f"计算热度分数失败: {e}")
        return float(solution.like_count * 2 + solution.view_count * 0.1)


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


async def get_solutions_with_usernames(
    db: AsyncSession, solutions: List[Solution]
) -> List[dict]:
    """
    批量获取题解并添加用户名（优化 N+1 查询）

    通过一次性查询所有用户，避免每个题解都查一次用户表
    """
    if not solutions:
        return []

    # 收集所有唯一的 user_id
    user_ids = list(set(s.user_id for s in solutions))

    # 一次性查询所有用户
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u.username for u in result.scalars().all()}

    # 组装结果
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "username": users.get(s.user_id, "未知用户"),
            "title": s.title,
            "content": s.content,
            "problem_link": s.problem_link,
            "tags": s.tags or [],
            "is_pinned": s.is_pinned,
            "is_announcement": s.is_announcement,
            "view_count": s.view_count,
            "like_count": s.like_count,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "hot_score": calculate_hot_score(s),
        }
        for s in solutions
    ]


async def create_solution(
    db: AsyncSession, solution_data: SolutionCreate, user_id: str
) -> Solution:
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
    logger.info(f"用户 {user_id} 创建了题解: {solution_data.title}")
    return db_solution


async def get_solutions(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    sort: str = "hot",
) -> Tuple[List[Solution], int]:
    """获取题解列表，支持排序"""
    # 获取总数
    count_result = await db.execute(select(func.count()).select_from(Solution))
    total = count_result.scalar_one()

    # 构建查询
    query = select(Solution)

    if sort == "new":
        query = query.order_by(desc(Solution.created_at))
    elif sort == "pinned":
        query = query.where(Solution.is_pinned == True).order_by(
            desc(Solution.created_at)
        )
    else:  # hot
        query = query.order_by(
            desc(Solution.is_pinned),
            desc(Solution.like_count),
            desc(Solution.view_count),
            desc(Solution.created_at),
        )

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    solutions = result.scalars().all()

    return list(solutions), total


async def get_solution_by_id(db: AsyncSession, solution_id: int) -> Optional[Solution]:
    """获取单个题解"""
    result = await db.execute(select(Solution).where(Solution.id == solution_id))
    return result.scalar_one_or_none()


async def update_solution(
    db: AsyncSession, solution: Solution, update_data: SolutionUpdate
) -> Solution:
    """更新题解"""
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(solution, key, value)
    await db.commit()
    await db.refresh(solution)
    logger.info(f"题解 {solution.id} 已更新")
    return solution


async def delete_solution(db: AsyncSession, solution: Solution) -> None:
    """删除题解"""
    solution_id = solution.id
    await db.delete(solution)
    await db.commit()
    logger.info(f"题解 {solution_id} 已删除")


async def toggle_like(db: AsyncSession, solution: Solution, user_id: str) -> Solution:
    """点赞/取消点赞（每人只能点赞一次）"""
    # 先尝试查找是否已点赞
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
        logger.info(f"用户 {user_id} 取消点赞题解 {solution.id}，当前点赞数: {solution.like_count}")
    else:
        # 未点赞，先确保 solution.like_count 已同步（处理并发情况）
        actual_count = await db.execute(
            select(func.count()).select_from(SolutionLike).where(SolutionLike.solution_id == solution.id)
        )
        solution.like_count = actual_count.scalar() + 1
        new_like = SolutionLike(user_id=user_id, solution_id=solution.id)
        db.add(new_like)
        logger.info(f"用户 {user_id} 点赞题解 {solution.id}，当前点赞数: {solution.like_count}")

    await db.commit()
    await db.refresh(solution)
    return solution


async def toggle_pin(db: AsyncSession, solution: Solution) -> Solution:
    """切换置顶状态"""
    solution.is_pinned = not solution.is_pinned
    await db.commit()
    await db.refresh(solution)
    status = "置顶" if solution.is_pinned else "取消置顶"
    logger.info(f"题解 {solution.id} {status}")
    return solution


async def increment_view(db: AsyncSession, solution: Solution) -> Solution:
    """增加浏览数"""
    solution.view_count += 1
    await db.commit()
    await db.refresh(solution)
    return solution
