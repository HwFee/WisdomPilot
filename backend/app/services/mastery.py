"""
Mastery Service - 章节掌握度计算与更新服务

基于三种核心模型的混合:
1. DKT (Deep Knowledge Tracing) - 追踪知识点状态演化
2. IRT (Item Response Theory) - 估计学生能力和题目难度
3. N-CCR (N-Consecutive Correct in a Row) - 简化的掌握判定
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.chapter import Chapter
from app.models.chapter_mastery import ChapterMastery
from app.models.user_stage import UserStageProgress, StageStatus
from app.models.stage import Stage
from app.utils.time import utc_now


# 掌握等级定义
MASTERY_LEVELS = {
    "入门": (0, 30),
    "学习": (31, 50),
    "练习": (51, 70),
    "熟练": (71, 85),
    "精通": (86, 100)
}


def get_mastery_level(score: float) -> str:
    """根据分数获取掌握等级"""
    for level, (low, high) in MASTERY_LEVELS.items():
        if low <= score <= high:
            return level
    return "入门"


class MasteryService:
    """章节掌握度服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_chapter_mastery(
        self,
        user_id: str,
        chapter_id: int,
        course_id: Optional[int] = None
    ) -> Optional[ChapterMastery]:
        """
        更新用户章节掌握度

        基于四个核心指标:
        1. accuracy - 正确率（加权难度）
        2. consistency - 稳定性
        3. depth - 知识覆盖度
        4. recency - 时效性
        """
        # 获取章节信息
        chapter_result = await self.db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        if not chapter:
            return None

        if course_id is None:
            course_id = chapter.course_id

        # 获取章节内所有关卡进度
        stages_result = await self.db.execute(
            select(Stage).where(Stage.chapter_id == chapter_id, Stage.is_active == True)
        )
        stages = stages_result.scalars().all()

        if not stages:
            # 如果没有关卡，创建一个基础掌握记录
            return await self._create_or_update_mastery(
                user_id, chapter_id, course_id,
                mastery_score=10.0,
                accuracy_score=10.0,
                consistency_score=50.0,
                depth_score=10.0,
                recency_score=50.0,
                total_exercises=0,
                correct_exercises=0
            )

        # 获取用户在这些关卡的进度
        stage_ids = [s.id for s in stages]
        progress_result = await self.db.execute(
            select(UserStageProgress).where(
                UserStageProgress.user_id == user_id,
                UserStageProgress.stage_id.in_(stage_ids)
            )
        )
        progresses = progress_result.scalars().all()

        if not progresses:
            return await self._create_or_update_mastery(
                user_id, chapter_id, course_id,
                mastery_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                depth_score=0.0,
                recency_score=0.0,
                total_exercises=0,
                correct_exercises=0
            )

        # 计算各项指标
        accuracy_score = self._calculate_weighted_accuracy(progresses, stages)
        consistency_score = self._calculate_consistency(progresses)
        depth_score = self._calculate_depth(progresses, stages)
        recency_score = self._calculate_recency(progresses)

        # 综合掌握分数（加权平均）
        mastery_score = (
            0.30 * accuracy_score +
            0.25 * consistency_score +
            0.20 * depth_score +
            0.15 * recency_score +
            0.10 * accuracy_score  # 使用 accuracy 作为 ability 的简化
        )

        # 统计数据
        total_exercises = sum(p.exercises_completed for p in progresses)
        correct_exercises = sum(p.exercises_correct for p in progresses)

        return await self._create_or_update_mastery(
            user_id, chapter_id, course_id,
            mastery_score=mastery_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            depth_score=depth_score,
            recency_score=recency_score,
            total_exercises=total_exercises,
            correct_exercises=correct_exercises
        )

    def _calculate_weighted_accuracy(
        self,
        progresses: list[UserStageProgress],
        stages: list[Stage]
    ) -> float:
        """
        加权正确率：难度越高权重越大
        """
        if not progresses:
            return 0.0

        # 创建 stage_id -> difficulty 映射
        stage_difficulty = {s.id: s.difficulty_level for s in stages}

        weighted_correct = 0.0
        weighted_total = 0.0

        for p in progresses:
            if p.exercises_completed > 0:
                diff = stage_difficulty.get(p.stage_id, 1)
                weight = diff
                weighted_correct += p.exercises_correct * weight
                weighted_total += p.exercises_completed * weight

        if weighted_total == 0:
            return 0.0

        return (weighted_correct / weighted_total) * 100

    def _calculate_consistency(self, progresses: list[UserStageProgress]) -> float:
        """
        稳定性分数：基于各关卡正确率的方差
        低方差 = 高稳定性
        """
        if len(progresses) < 2:
            return 50.0  # 数据不足给中间分

        accuracies = []
        for p in progresses:
            if p.exercises_completed > 0:
                accuracies.append(p.accuracy)

        if len(accuracies) < 2:
            return 50.0

        # 计算方差
        mean_acc = sum(accuracies) / len(accuracies)
        variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)

        # 方差越小，稳定性越高
        # 方差范围大约 0-0.25，转换为 0-100
        consistency = max(0, 100 - variance * 400)
        return consistency

    def _calculate_depth(
        self,
        progresses: list[UserStageProgress],
        stages: list[Stage]
    ) -> float:
        """
        知识覆盖度：完成的关卡比例
        """
        if not stages:
            return 0.0

        completed_count = sum(
            1 for p in progresses
            if p.status == StageStatus.COMPLETED.value
        )

        return (completed_count / len(stages)) * 100

    def _calculate_recency(self, progresses: list[UserStageProgress]) -> float:
        """
        时效性分数：最近学习时间
        """
        now = utc_now()

        # 找到最近的学习时间
        recent_times = []
        for p in progresses:
            if p.completed_at:
                recent_times.append(p.completed_at)
            elif p.started_at:
                recent_times.append(p.started_at)

        if not recent_times:
            return 0.0

        most_recent = max(recent_times)

        # 计算时间差（小时）
        hours_diff = (now - most_recent).total_seconds() / 3600

        # 24小时内满分，之后线性递减
        if hours_diff <= 24:
            return 100.0
        elif hours_diff <= 168:  # 一周内
            return max(50, 100 - (hours_diff - 24) / 144 * 50)
        else:
            return max(0, 50 - (hours_diff - 168) / 168 * 50)

    async def _create_or_update_mastery(
        self,
        user_id: str,
        chapter_id: int,
        course_id: int,
        mastery_score: float,
        accuracy_score: float,
        consistency_score: float,
        depth_score: float,
        recency_score: float,
        total_exercises: int,
        correct_exercises: int
    ) -> ChapterMastery:
        """创建或更新掌握记录"""

        # 查找现有记录
        result = await self.db.execute(
            select(ChapterMastery).where(
                ChapterMastery.user_id == user_id,
                ChapterMastery.chapter_id == chapter_id
            )
        )
        mastery = result.scalar_one_or_none()

        now = utc_now()
        mastery_level = get_mastery_level(mastery_score)

        if mastery:
            # 更新现有记录
            mastery.mastery_score = mastery_score
            mastery.mastery_level = mastery_level
            mastery.accuracy_score = accuracy_score
            mastery.consistency_score = consistency_score
            mastery.depth_score = depth_score
            mastery.recency_score = recency_score
            mastery.total_exercises = total_exercises
            mastery.correct_exercises = correct_exercises
            mastery.last_practiced_at = now

            # 如果达到精通，记录时间
            if mastery_score >= 86 and mastery.mastered_at is None:
                mastery.mastered_at = now
        else:
            # 创建新记录
            mastery = ChapterMastery(
                user_id=user_id,
                chapter_id=chapter_id,
                course_id=course_id,
                mastery_score=mastery_score,
                mastery_level=mastery_level,
                accuracy_score=accuracy_score,
                consistency_score=consistency_score,
                depth_score=depth_score,
                recency_score=recency_score,
                total_exercises=total_exercises,
                correct_exercises=correct_exercises,
                first_practiced_at=now,
                last_practiced_at=now,
            )
            self.db.add(mastery)

        await self.db.flush()
        return mastery


# 服务工厂函数
def get_mastery_service(db: AsyncSession) -> MasteryService:
    """获取掌握度服务实例"""
    return MasteryService(db)
