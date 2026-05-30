"""WrongQuestion Service - 错题收集与管理服务"""

from typing import Optional, List, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.wrong_question import WrongQuestion
from app.models.exercise import Exercise
from app.models.user_weak_point import UserWeakPoint
from app.models.spaced_repetition import SpacedRepetition
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


class WrongQuestionService:
    """错题收集与管理服务

    职责：
    1. 收集错题（去重逻辑：相同题目只记录一次，更新错误次数和时间）
    2. 解决错题（答对后标记）
    3. 关联更新薄弱点（UserWeakPoint）
    4. 创建复习计划（SpacedRepetition）
    """

    def _extract_base_exercise_key(self, exercise_key: str) -> str:
        """从 exercise_key 中提取基础标识用于去重

        exercise_key 格式:
        - 精进之路基础题: mastery-${courseId}-${chapterId}-${questionId}
        - 强化测试题: enhanced-${courseId}-${sectionId}-${questionId}
        - 挑战之路: arena-${courseId}-${exerciseId}

        去重逻辑: 同一道题无论在哪个会话中，都应该合并记录
        - 精进之路基础题: 使用完整 key (包含章节信息)
        - 强化测试题: 使用完整 key (包含小节信息)
        - 挑战之路: 只使用 courseId 和 exerciseId (去掉 sessionId)
        """
        parts = exercise_key.split('-')
        if len(parts) < 3:
            return exercise_key

        prefix = parts[0]
        if prefix == 'arena':
            # arena-${courseId}-${exerciseId} -> 保持不变
            # 新旧格式均为 3 个 parts；旧格式的 sessionId 与 courseId 语义不同，
            # 统一提取最后一个 part 作为 exercise_id 以兼容历史数据。
            if len(parts) == 3:
                return exercise_key
            else:
                exercise_id = parts[-1]
                return f"arena-{exercise_id}"
        elif prefix == 'enhanced':
            # enhanced-${courseId}-${sectionId}-${questionId} -> 保持不变
            # 这样同一小节的同一道强化题会被合并
            return exercise_key
        else:
            # mastery 或其他格式保持不变
            return exercise_key

    async def collect_wrong_question_by_key(
        self,
        db: AsyncSession,
        user_id: str,
        exercise_key: str,
        user_answer: Any,
        course_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        section_id: Optional[int] = None,
        exercise_content: Optional[dict] = None,
        exercise_type: str = "choice",
        knowledge_points: Optional[List[str]] = None,
        exercise_id: Optional[int] = None,
    ) -> WrongQuestion:
        """通过 exercise_key 收集错题（用于前端硬编码习题）

        当前端使用硬编码习题（非数据库 Exercise）时，使用此方法。
        exercise_key 格式：chapterId-subsectionIndex-exerciseId 或 arena-global-{exerciseId}

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_key: 练习题标识（格式：chapterId-subsectionIndex-exerciseId 或 arena-global-{exerciseId}）
            user_answer: 用户答案
            course_id: 课程ID（可选，用于精进之路）
            chapter_id: 章节ID（可选）
            section_id: 小节ID（强化测试来源，可选）
            knowledge_points: 知识点列表
            exercise_id: 练习题真实ID（可选，用于挑战之路等数据库Exercise）

        Returns:
            WrongQuestion: 错题记录
        """
        logger.info(f"[collect_wrong_question_by_key] 开始收集: user_id={user_id}, exercise_key={exercise_key}, course_id={course_id}")
        base_key = self._extract_base_exercise_key(exercise_key)
        logger.info(f"[collect_wrong_question_by_key] 原始key={exercise_key}, 去重key={base_key}")

        # 检查是否已存在相同记录（同一用户同一基础标识）
        existing = await db.execute(
            select(WrongQuestion).where(
                and_(
                    WrongQuestion.user_id == user_id,
                    WrongQuestion.exercise_key == base_key,
                )
            )
        )
        wrong_question = existing.scalar_one_or_none()

        if wrong_question:
            # 已存在：记录新的错误
            wrong_question.record_error()
            # 更新答案记录（保留最近一次）
            wrong_question.user_answer = user_answer
            # 更新题目内容快照（可能题目已更新）
            if exercise_content:
                wrong_question.exercise_content = exercise_content
            logger.info(f"[collect_wrong_question_by_key] 更新已有错题记录: id={wrong_question.id}, error_count={wrong_question.error_count}")
        else:
            # 不存在：创建新记录（使用去重后的 base_key）
            wrong_question = WrongQuestion(
                user_id=user_id,
                exercise_id=exercise_id,  # 传入的真实 Exercise ID（如有）
                exercise_key=base_key,  # 存储去重后的 key
                course_id=course_id,
                chapter_id=chapter_id,
                section_id=section_id,
                knowledge_points=knowledge_points or [],
                user_answer=user_answer,
                correct_answer={},  # 前端硬编码习题没有标准答案存储
                exercise_content=exercise_content,
                exercise_type=exercise_type,
                error_count=1,
                is_resolved=False,
            )
            db.add(wrong_question)
            logger.info("[collect_wrong_question_by_key] 创建新错题记录")

        await db.flush()

        # 更新薄弱点记录
        if knowledge_points:
            await self._update_weak_points(
                db=db,
                user_id=user_id,
                knowledge_points=knowledge_points,
                course_id=course_id,
            )

        # 创建或更新复习计划（使用去重后的 base_key）
        await self._schedule_review(
            db=db,
            user_id=user_id,
            exercise_key=base_key,
        )

        return wrong_question

    async def collect_wrong_question(
        self,
        db: AsyncSession,
        user_id: str,
        exercise: Exercise,
        user_answer: Any,
        course_id: Optional[int] = None,
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
            course_id: 课程ID（可选，挑战之路没有课程关联）
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
        exercise_id: Optional[int] = None,
        exercise_key: Optional[str] = None,
    ) -> Optional[WrongQuestion]:
        """标记错题为已解决

        当用户答对某道曾经错误的题目时调用。
        支持通过 exercise_id 或 exercise_key 查找错题记录（精进/挑战之路的错题 exercise_id 为 None）。

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_id: 练习题ID（可选）
            exercise_key: 练习题标识（可选，用于精进之路/挑战之路等 exercise_id 为 None 的情况）

        Returns:
            Optional[WrongQuestion]: 被更新的错题记录，如果没有找到则返回None
        """
        conditions = [
            WrongQuestion.user_id == user_id,
        ]

        if exercise_id is not None:
            conditions.append(WrongQuestion.exercise_id == exercise_id)
        elif exercise_key is not None:
            conditions.append(WrongQuestion.exercise_key == exercise_key)
        else:
            return None

        result = await db.execute(
            select(WrongQuestion).where(and_(*conditions))
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
        course_id: Optional[int] = None,
    ) -> None:
        """更新薄弱点记录（记录错误）

        Args:
            db: 数据库会话
            user_id: 用户ID
            knowledge_points: 知识点列表
            course_id: 课程ID（可选）
        """
        for kp in knowledge_points:
            query = select(UserWeakPoint).where(
                and_(
                    UserWeakPoint.user_id == user_id,
                    UserWeakPoint.knowledge_point == kp,
                )
            )
            if course_id is not None:
                query = query.where(UserWeakPoint.course_id == course_id)

            result = await db.execute(query)
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
        exercise_id: Optional[int] = None,
        exercise_key: Optional[str] = None,
        stage_id: Optional[int] = None,
    ) -> Optional[SpacedRepetition]:
        """创建或更新复习计划

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_id: 练习题ID（真实数据库ID）
            exercise_key: 练习题标识（前端硬编码习题）
            stage_id: 关卡ID

        Returns:
            Optional[SpacedRepetition]: 复习计划记录
        """
        # 构建查询条件
        conditions = [SpacedRepetition.user_id == user_id]
        if exercise_id:
            conditions.append(SpacedRepetition.exercise_id == exercise_id)
        elif exercise_key:
            conditions.append(SpacedRepetition.exercise_key == exercise_key)
        else:
            return None  # 必须有 exercise_id 或 exercise_key

        # 检查是否已有复习计划
        result = await db.execute(
            select(SpacedRepetition).where(and_(*conditions))
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
            new_review = SpacedRepetition(
                user_id=user_id,
                exercise_id=exercise_id,
                exercise_key=exercise_key,
                stage_id=stage_id,
                next_review_at=utc_now(),
                review_interval=1,
                ease_factor=2.5,
                review_count=0
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
                not WrongQuestion.is_resolved,
            )
        )

        if course_id is not None:
            query = query.where(WrongQuestion.course_id == course_id)

        result = await db.execute(query)
        return result.scalar() or 0

    async def delete_wrong_question(
        self,
        db: AsyncSession,
        wrong_question_id: str,
        user_id: str,
    ) -> bool:
        """删除错题记录

        Args:
            db: 数据库会话
            wrong_question_id: 错题ID
            user_id: 用户ID（用于权限验证）

        Returns:
            bool: 是否删除成功
        """
        result = await db.execute(
            select(WrongQuestion).where(
                and_(
                    WrongQuestion.id == wrong_question_id,
                    WrongQuestion.user_id == user_id,
                )
            )
        )
        wrong_question = result.scalar_one_or_none()

        if wrong_question:
            await db.delete(wrong_question)
            await db.flush()
            return True
        return False


wrong_question_service = WrongQuestionService()
