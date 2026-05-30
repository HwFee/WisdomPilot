"""
Leaderboard Service - 排行榜服务

支持两种榜单:
1. 精进榜 (Mastery Board) - 基于章节掌握进度
2. 竞技榜 (Arena Board) - 基于用户总经验值
"""

from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.chapter_mastery import ChapterMastery
import logging


class LeaderboardEntry:
    """排行榜条目"""
    def __init__(
        self,
        rank: int,
        user_id: str,
        username: str,
        score: float,
        extra_info: dict = None
    ):
        self.rank = rank
        self.user_id = user_id
        self.username = username
        self.score = score
        self.extra_info = extra_info or {}


class LeaderboardService:
    """排行榜服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_mastery_leaderboard(
        self,
        course_id: int,
        limit: int = 50
    ) -> List[LeaderboardEntry]:
        """
        获取精进榜

        排名依据：
        1. 总掌握分数（加权求和）
        2. 掌握章节数
        3. 平均掌握度
        """
        # 按用户聚合掌握分数
        query = (
            select(
                ChapterMastery.user_id,
                func.sum(ChapterMastery.mastery_score).label("total_score"),
                func.count(ChapterMastery.id).label("chapter_count"),
                func.avg(ChapterMastery.mastery_score).label("avg_score")
            )
            .where(ChapterMastery.course_id == course_id)
            .group_by(ChapterMastery.user_id)
            .order_by(desc("total_score"))
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 获取用户名
        user_ids = [row.user_id for row in rows]
        users_result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {u.id: u.username for u in users_result.scalars().all()}

        # 构建排行榜
        entries = []
        for i, row in enumerate(rows):
            entries.append(LeaderboardEntry(
                rank=i + 1,
                user_id=row.user_id,
                username=users_map.get(row.user_id, "未知用户"),
                score=row.total_score,
                extra_info={
                    "chapter_count": row.chapter_count,
                    "avg_score": round(row.avg_score, 2)
                }
            ))

        return entries

    async def get_arena_leaderboard(
        self,
        course_id: Optional[int] = None,
        limit: int = 50
    ) -> List[LeaderboardEntry]:
        """
        获取竞技榜

        排名依据：
        1. 用户总经验值 (total_xp)
        2. 正确题目数
        """
        # 基于用户表的 total_xp 排序
        query = (
            select(User)
            .where(User.total_xp > 0)
            .order_by(desc(User.total_xp))
            .limit(limit)
        )

        result = await self.db.execute(query)
        users = result.scalars().all()

        # 构建排行榜
        entries = []
        for i, user in enumerate(users):
            entries.append(LeaderboardEntry(
                rank=i + 1,
                user_id=user.id,
                username=user.username,
                score=float(user.total_xp or 0),
                extra_info={
                    "correct_exercises": user.correct_exercises or 0,
                    "total_exercises": user.total_exercises or 0,
                    "accuracy": round(user.accuracy_rate * 100, 2) if user.accuracy_rate else 0
                }
            ))

        return entries

    async def update_user_rank(
        self,
        user_id: str,
        course_id: int
    ) -> Optional[int]:
        """
        更新用户排名

        返回用户在精进榜中的排名
        """
        # 计算用户总分
        query = (
            select(func.sum(ChapterMastery.mastery_score))
            .where(
                ChapterMastery.user_id == user_id,
                ChapterMastery.course_id == course_id
            )
        )
        result = await self.db.execute(query)
        user_score = result.scalar() or 0

        if user_score == 0:
            return None

        # 计算排名（有多少人分数比用户高）
        rank_query = (
            select(func.count())
            .select_from(
                select(ChapterMastery.user_id)
                .where(ChapterMastery.course_id == course_id)
                .group_by(ChapterMastery.user_id)
                .having(func.sum(ChapterMastery.mastery_score) > user_score)
            )
        )
        rank_result = await self.db.execute(rank_query)
        higher_count = rank_result.scalar() or 0

        return higher_count + 1


# 服务工厂函数
def get_leaderboard_service(db: AsyncSession) -> LeaderboardService:
    """获取排行榜服务实例"""
    return LeaderboardService(db)


logger = logging.getLogger(__name__)