"""WrongQuestion Service - 错题收集与管理服务"""

from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wrong_question import WrongQuestion
from app.models.exercise import Exercise
from app.models.user_weak_point import UserWeakPoint
from app.models.spaced_repetition import SpacedRepetition
from app.utils.time import utc_now


class WrongQuestionService:
    """错题收集与管理服务

    职责：
    1. 收集错题（去重逻辑：相同题目只记录一次，更新错误次数和时间）
    2. 解决错题（答对后标记）
    3. 关联更新薄弱点（UserWeakPoint）
    4. 创建复习计划（SpacedRepetition）
    """

    async def collect_wrong_question(
        self,
        db: AsyncSession,
        user_id: str,
        exercise: Exercise,
        user_answer: Any,
        course_id: int,
        chapter_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        challenge_session_id: Optional[str] = None,
    ) -> WrongQuestion:
        """收集错题

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise: 练习题对象
            user_answer: 用户答案
            course_id: 课程ID
            chapter_id: 章节ID
            stage_id: 关卡ID（精进之路来源）
            challenge_session_id: 挑战会话ID（挑战之路来源）

        Returns:
            WrongQuestion: 错题记录
        """
        # 检查是否已存在相同记录（同一用户同一题目）
        existing = await db.execute(
            select(WrongQuestion).where(
                and_(
                    WrongQuestion.user_id == user_id,
                    WrongQuestion.exercise_id == exercise.id,
                )
            )
        )
        wrong_question = existing.scalar_one_or_none()

        if wrong_question:
            # 已存在：记录新的错误
            wrong_question.record_error()
            # 更新答案记录（保留最近一次）
            wrong_question.user_answer = user_answer
            wrong_question.correct_answer = exercise.solution.get("answer") if exercise.solution else {}
        else:
            # 不存在：创建新记录
            wrong_question = WrongQuestion(
                user_id=user_id,
                exercise_id=exercise.id,
                course_id=course_id,
                chapter_id=chapter_id,
                stage_id=stage_id,
                challenge_session_id=challenge_session_id,
                knowledge_points=exercise.knowledge_points or [],
                user_answer=user_answer,
                correct_answer=exercise.solution.get("answer") if exercise.solution else {},
                exercise_content=exercise.content,
                exercise_type=exercise.type,
                exercise_difficulty=exercise.difficulty,
                error_count=1,
                is_resolved=False,
            )
            db.add(wrong_question)

        await db.flush()

        # 更新薄弱点记录
        await self._update_weak_points(
            db=db,
            user_id=user_id,
            knowledge_points=exercise.knowledge_points or [],
            course_id=course_id,
        )

        # 创建或更新复习计划
        await self._schedule_review(
            db=db,
            user_id=user_id,
            exercise_id=exercise.id,
            stage_id=stage_id,
        )

        return wrong_question

    async def mark_resolved(
        self,
        db: AsyncSession,
        user_id: str,
        exercise_id: int,
    ) -> Optional[WrongQuestion]:
        """标记错题为已解决

        当用户答对某道曾经错误的题目时调用。

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_id: 练习题ID

        Returns:
            Optional[WrongQuestion]: 被更新的错题记录，如果没有找到则返回None
        """
        result = await db.execute(
            select(WrongQuestion).where(
                and_(
                    WrongQuestion.user_id == user_id,
                    WrongQuestion.exercise_id == exercise_id,
                )
            )
        )
        wrong_question = result.scalar_one_or_none()

        if wrong_question:
            wrong_question.mark_resolved()
            await db.flush()

            # 更新薄弱点（复习成功，提高掌握程度）
            await self._update_weak_points_on_review(
                db=db,
                user_id=user_id,
                knowledge_points=wrong_question.knowledge_points,
                course_id=wrong_question.course_id,
                success=True,
            )

        return wrong_question

    async def _update_weak_points(
        self,
        db: AsyncSession,
        user_id: str,
        knowledge_points: List[str],
        course_id: int,
    ) -> None:
        """更新薄弱点记录（记录错误）

        Args:
            db: 数据库会话
            user_id: 用户ID
            knowledge_points: 知识点列表
            course_id: 课程ID
        """
        for kp in knowledge_points:
            result = await db.execute(
                select(UserWeakPoint).where(
                    and_(
                        UserWeakPoint.user_id == user_id,
                        UserWeakPoint.course_id == course_id,
                        UserWeakPoint.knowledge_point == kp,
                    )
                )
            )
            weak_point = result.scalar_one_or_none()

            if weak_point:
                weak_point.record_error()
            else:
                # 创建新的薄弱点记录
                weak_point = UserWeakPoint(
                    user_id=user_id,
                    course_id=course_id,
                    knowledge_point=kp,
                    error_count=1,
                    mastery_level=1,  # 新错误，默认最低掌握程度
                )
                db.add(weak_point)

        await db.flush()

    async def _update_weak_points_on_review(
        self,
        db: AsyncSession,
        user_id: str,
        knowledge_points: List[str],
        course_id: int,
        success: bool,
    ) -> None:
        """更新薄弱点记录（复习后）

        Args:
            db: 数据库会话
            user_id: 用户ID
            knowledge_points: 知识点列表
            course_id: 课程ID
            success: 是否成功（答对）
        """
        for kp in knowledge_points:
            result = await db.execute(
                select(UserWeakPoint).where(
                    and_(
                        UserWeakPoint.user_id == user_id,
                        UserWeakPoint.course_id == course_id,
                        UserWeakPoint.knowledge_point == kp,
                    )
                )
            )
            weak_point = result.scalar_one_or_none()

            if weak_point:
                weak_point.record_review(success=success)

        await db.flush()

    async def _schedule_review(
        self,
        db: AsyncSession,
        user_id: str,
        exercise_id: int,
        stage_id: Optional[int] = None,
    ) -> Optional[SpacedRepetition]:
        """创建或更新复习计划

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_id: 练习题ID
            stage_id: 关卡ID

        Returns:
            Optional[SpacedRepetition]: 复习计划记录
        """
        # 检查是否已有复习计划
        result = await db.execute(
            select(SpacedRepetition).where(
                and_(
                    SpacedRepetition.user_id == user_id,
                    SpacedRepetition.exercise_id == exercise_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 已有复习计划：重置间隔（因为答错了，需要重新学习）
            existing.review_interval = 1
            existing.next_review_at = utc_now()
            existing.last_review_result = False
            return existing
        else:
            # 创建新的复习计划
            new_review = SpacedRepetition.create_new(
                user_id=user_id,
                exercise_id=exercise_id,
                stage_id=stage_id,
            )
            db.add(new_review)
            await db.flush()
            return new_review

    async def get_user_wrong_questions(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[WrongQuestion], int]:
        """获取用户的错题列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID（可选）
            chapter_id: 章节ID（可选）
            is_resolved: 是否已解决（可选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            tuple[List[WrongQuestion], int]: (错题列表, 总数)
        """
        query = select(WrongQuestion).where(WrongQuestion.user_id == user_id)

        if course_id is not None:
            query = query.where(WrongQuestion.course_id == course_id)
        if chapter_id is not None:
            query = query.where(WrongQuestion.chapter_id == chapter_id)
        if is_resolved is not None:
            query = query.where(WrongQuestion.is_resolved == is_resolved)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 获取分页数据
        query = query.order_by(WrongQuestion.last_error_at.desc())
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        wrong_questions = list(result.scalars().all())

        return wrong_questions, total

    async def get_wrong_question_by_id(
        self,
        db: AsyncSession,
        wrong_question_id: str,
        user_id: str,
    ) -> Optional[WrongQuestion]:
        """获取单个错题详情

        Args:
            db: 数据库会话
            wrong_question_id: 错题ID
            user_id: 用户ID（用于权限验证）

        Returns:
            Optional[WrongQuestion]: 错题记录
        """
        result = await db.execute(
            select(WrongQuestion).where(
                and_(
                    WrongQuestion.id == wrong_question_id,
                    WrongQuestion.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_wrong_question_by_exercise(
        self,
        db: AsyncSession,
        user_id: str,
        exercise_id: int,
    ) -> Optional[WrongQuestion]:
        """根据题目ID获取错题记录

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_id: 练习题ID

        Returns:
            Optional[WrongQuestion]: 错题记录
        """
        result = await db.execute(
            select(WrongQuestion).where(
                and_(
                    WrongQuestion.user_id == user_id,
                    WrongQuestion.exercise_id == exercise_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_wrong_count(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: Optional[int] = None,
    ) -> int:
        """获取用户的错题数量

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID（可选）

        Returns:
            int: 错题数量
        """
        query = select(func.count()).select_from(WrongQuestion).where(
            WrongQuestion.user_id == user_id
        )

        if course_id is not None:
            query = query.where(WrongQuestion.course_id == course_id)

        result = await db.execute(query)
        return result.scalar() or 0

    async def get_unresolved_count(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: Optional[int] = None,
    ) -> int:
        """获取用户的未解决错题数量

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID（可选）

        Returns:
            int: 未解决错题数量
        """
        query = select(func.count()).select_from(WrongQuestion).where(
            and_(
                WrongQuestion.user_id == user_id,
                WrongQuestion.is_resolved == False,
            )
        )

        if course_id is not None:
            query = query.where(WrongQuestion.course_id == course_id)

        result = await db.execute(query)
        return result.scalar() or 0


wrong_question_service = WrongQuestionService()
