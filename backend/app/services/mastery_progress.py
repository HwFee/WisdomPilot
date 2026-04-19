"""
Mastery Progress Service - 精进之路进度服务

提供：
1. 保存精进之路做题进度
2. 获取章节进度
3. 完成章节quiz时更新ChapterMastery
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter_base_question import ChapterBaseQuestion
from app.models.chapter_mastery import ChapterMastery
from app.models.mastery_exercise_progress import MasteryExerciseProgress
from app.models.stats import ActivityLog
from app.schemas.mastery_progress import (
    MasteryChapterProgressResponse,
    MasteryExerciseProgressResponse,
    MasteryExerciseProgressSaveRequest,
    MasteryQuizCompleteRequest,
)
from app.utils.time import utc_now
from app.services.core_service import CoreService


class MasteryProgressService:
    """精进之路进度服务"""

    async def save_exercise_progress(
        self,
        db: AsyncSession,
        user_id: str,
        request: MasteryExerciseProgressSaveRequest,
    ) -> MasteryExerciseProgressResponse:
        """
        保存精进之路做题进度

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 进度保存请求

        Returns:
            保存结果
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[save_exercise_progress] 开始处理 user={user_id[:8]}..., question={request.question_id}, is_correct={request.is_correct}")

        try:
            # 构建exercise_key
            if not request.exercise_key:
                request.exercise_key = f"mastery-{request.course_id}-{request.chapter_id}-{request.question_id}"

            # 使用 upsert 逻辑：存在则更新，不存在则创建
            result = await db.execute(
                select(MasteryExerciseProgress).where(
                    and_(
                        MasteryExerciseProgress.user_id == user_id,
                        MasteryExerciseProgress.course_id == request.course_id,
                        MasteryExerciseProgress.chapter_id == request.chapter_id,
                        MasteryExerciseProgress.question_id == request.question_id,
                        MasteryExerciseProgress.question_type == request.question_type,
                    )
                )
            )
            progress = result.scalar_one_or_none()

            # 判断是否应该发放智核奖励（首次答对）
            should_award_cores = False
            if request.is_correct:
                if progress:
                    # 已有记录，检查是否首次答对
                    if not progress.correct_at:
                        should_award_cores = True
                        logger.info(f"[save_exercise_progress] 已有记录但未答对过，将发放智核")
                    else:
                        logger.info(f"[save_exercise_progress] 已答对过，不重复发放智核")
                else:
                    # 新记录，首次答对
                    should_award_cores = True
                    logger.info(f"[save_exercise_progress] 新记录，将发放智核")

            if progress:
                # 更新已有记录
                progress.is_completed = request.is_completed
                progress.is_correct = request.is_correct
                if request.user_answer:
                    progress.user_answer = request.user_answer
                if request.correct_answer:
                    progress.correct_answer = request.correct_answer
                progress.attempt_count += request.attempt_count
                progress.last_attempt_at = utc_now()
                if request.is_correct and not progress.correct_at:
                    progress.correct_at = utc_now()
            else:
                # 创建新记录
                progress = MasteryExerciseProgress(
                    user_id=user_id,
                    course_id=request.course_id,
                    chapter_id=request.chapter_id,
                    question_id=request.question_id,
                    question_type=request.question_type,
                    exercise_key=request.exercise_key,
                    is_completed=request.is_completed,
                    is_correct=request.is_correct,
                    user_answer=request.user_answer,
                    correct_answer=request.correct_answer,
                    attempt_count=request.attempt_count,
                    first_attempt_at=utc_now(),
                    last_attempt_at=utc_now(),
                    correct_at=utc_now() if request.is_correct else None,
                )
                db.add(progress)

            question_result = await db.execute(
                select(ChapterBaseQuestion).where(
                    ChapterBaseQuestion.id == request.question_id
                )
            )
            question = question_result.scalar_one_or_none()

            # 调试日志：记录题目信息
            logger.info(f"[save_exercise_progress] 题目查询结果: question_id={request.question_id}, found={question is not None}")
            if question:
                logger.info(f"[save_exercise_progress] 题目详情: db_id={question.id}, order_index={question.order_index}, question_source={question.question_source}, question_type={request.question_type}")

            # 根据题目类型确定标题，使用 order_index 作为编号
            if question:
                if request.question_type == "enhanced":
                    question_title = f"强化题 {question.order_index}"
                else:
                    question_title = f"基础题 {question.order_index}"
            else:
                question_title = f"题目 {request.question_id}"

            logger.info(f"[save_exercise_progress] 生成标题: question_title={question_title}, question_id={request.question_id}, order_index={question.order_index if question else None}")

            activity = ActivityLog(
                user_id=user_id,
                activity_type="exercise_complete",
                chapter_id=request.chapter_id,
                description=f"精进之路完成{question_title}",
                extra_data={
                    "learning_path": "mastery",
                    "learning_path_label": "精进之路",
                    "exercise_id": request.question_id,
                    "exercise_title": question_title,
                    "question_type": request.question_type,
                    "is_correct": request.is_correct,
                    "course_id": request.course_id,
                    "chapter_id": request.chapter_id,
                    "exercise_key": request.exercise_key,
                },
            )
            db.add(activity)
            logger.info(f"[save_exercise_progress] 已创建活动记录: activity_type=exercise_complete, exercise_id={request.question_id}, exercise_title={question_title}")

            # 首次答对时发放智核奖励（每题2个智核）
            core_earned = False
            if should_award_cores:
                try:
                    core_service = CoreService(db)
                    logger.info(f"[save_exercise_progress] 发放智核: user={user_id[:8]}..., question={request.question_id}, amount=2")
                    await core_service.earn_cores(
                        user_id=user_id,
                        amount=2,
                        category="mastery",
                        reference_type="exercise",
                        reference_id=str(request.question_id),
                        description=f"精进之路答对{question_title}",
                    )
                    core_earned = True
                    logger.info(f"[save_exercise_progress] 智核发放成功")
                except Exception as core_error:
                    # 智核发放失败不应影响进度保存，记录错误即可
                    logger.error(f"[save_exercise_progress] 智核发放失败: {core_error}")

            await db.commit()
            logger.info(f"[save_exercise_progress] 完成, core_earned={core_earned}")
            return MasteryExerciseProgressResponse(
                success=True,
                progress_id=progress.id,
                message="进度保存成功" + ("，获得2智核" if core_earned else "")
            )

        except Exception as e:
            await db.rollback()
            return MasteryExerciseProgressResponse(
                success=False, message=f"保存失败: {str(e)}"
            )

    async def get_chapter_progress(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: int,
        chapter_id: int,
    ) -> MasteryChapterProgressResponse:
        """
        获取章节进度

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID
            chapter_id: 章节ID

        Returns:
            章节进度
        """
        # 获取章节总题数
        questions_result = await db.execute(
            select(ChapterBaseQuestion).where(
                ChapterBaseQuestion.chapter_id == chapter_id,
                ChapterBaseQuestion.is_active == True,
            )
        )
        total_questions = len(questions_result.scalars().all())

        # 获取用户在该章节的进度
        progress_result = await db.execute(
            select(MasteryExerciseProgress).where(
                and_(
                    MasteryExerciseProgress.user_id == user_id,
                    MasteryExerciseProgress.course_id == course_id,
                    MasteryExerciseProgress.chapter_id == chapter_id,
                    MasteryExerciseProgress.question_type == "base",
                )
            )
        )
        progress_list = progress_result.scalars().all()

        completed_questions = sum(1 for p in progress_list if p.is_completed)
        correct_questions = sum(1 for p in progress_list if p.is_correct)

        # 计算掌握度
        mastery_score = 0.0
        if total_questions > 0:
            mastery_score = (correct_questions / total_questions) * 100

        return MasteryChapterProgressResponse(
            chapter_id=chapter_id,
            total_questions=total_questions,
            completed_questions=completed_questions,
            correct_questions=correct_questions,
            mastery_score=mastery_score,
            is_passed=mastery_score >= 80,
        )

    async def complete_chapter_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: MasteryQuizCompleteRequest,
    ) -> bool:
        """
        完成章节quiz时更新ChapterMastery

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 完成quiz请求

        Returns:
            是否成功
        """
        try:
            # 获取章节信息
            questions_result = await db.execute(
                select(ChapterBaseQuestion).where(
                    ChapterBaseQuestion.chapter_id == request.chapter_id,
                    ChapterBaseQuestion.is_active == True,
                )
            )
            questions = {q.id: q for q in questions_result.scalars().all()}

            # 统计正确率
            correct_count = 0
            total_count = len(questions)
            knowledge_correct = {}
            knowledge_total = {}

            for result in request.results:
                question_id = result.get("question_id")
                is_correct = result.get("is_correct", False)
                question = questions.get(question_id)

                if is_correct:
                    correct_count += 1

                # 统计知识点
                if question and question.knowledge_points:
                    for kp in question.knowledge_points:
                        if kp not in knowledge_total:
                            knowledge_total[kp] = 0
                            knowledge_correct[kp] = 0
                        knowledge_total[kp] += 1
                        if is_correct:
                            knowledge_correct[kp] += 1

            accuracy = correct_count / total_count if total_count > 0 else 0

            # 获取或创建ChapterMastery
            mastery_result = await db.execute(
                select(ChapterMastery).where(
                    and_(
                        ChapterMastery.user_id == user_id,
                        ChapterMastery.chapter_id == request.chapter_id,
                    )
                )
            )
            mastery = mastery_result.scalar_one_or_none()

            if mastery:
                # 更新已有记录
                mastery.total_exercises += total_count
                mastery.correct_exercises += correct_count
                if mastery.total_exercises > 0:
                    mastery.accuracy_score = (
                        mastery.correct_exercises / mastery.total_exercises
                    ) * 100
                mastery.mastery_score = min(100, mastery.mastery_score + (accuracy * 5))
                from app.services.chapter_mastery import ChapterMasteryService

                service = ChapterMasteryService(None)
                mastery.mastery_level = service.get_mastery_level(mastery.mastery_score)
                mastery.last_practiced_at = utc_now()
                if mastery.mastery_score >= 85 and not mastery.mastered_at:
                    mastery.mastered_at = utc_now()
            else:
                # 创建新记录
                from app.services.chapter_mastery import ChapterMasteryService

                service = ChapterMasteryService(None)
                mastery = ChapterMastery(
                    user_id=user_id,
                    course_id=request.course_id,
                    chapter_id=request.chapter_id,
                    total_exercises=total_count,
                    correct_exercises=correct_count,
                    accuracy_score=accuracy * 100,
                    mastery_score=min(100, accuracy * 30),
                    mastery_level=service.get_mastery_level(accuracy * 30),
                    first_practiced_at=utc_now(),
                    last_practiced_at=utc_now(),
                )
                if accuracy * 30 >= 85:
                    mastery.mastered_at = utc_now()
                db.add(mastery)

            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            print(f"Failed to complete chapter quiz: {e}")
            return False

    async def get_progress_by_exercise_key(
        self,
        db: AsyncSession,
        user_id: str,
        exercise_key: str,
    ) -> Optional[MasteryExerciseProgress]:
        """根据exercise_key获取进度"""
        result = await db.execute(
            select(MasteryExerciseProgress).where(
                and_(
                    MasteryExerciseProgress.user_id == user_id,
                    MasteryExerciseProgress.exercise_key == exercise_key,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_chapter_detail_progress(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: int,
        chapter_id: int,
    ):
        """
        获取章节详细进度 - 包含每道题的进度信息

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID
            chapter_id: 章节ID

        Returns:
            章节详细进度，包含每道题的进度
        """
        from app.schemas.mastery_progress import (
            MasteryChapterDetailProgressResponse,
            MasteryExerciseProgressItem,
        )

        # 获取章节总题数
        questions_result = await db.execute(
            select(ChapterBaseQuestion)
            .where(
                ChapterBaseQuestion.chapter_id == chapter_id,
                ChapterBaseQuestion.is_active == True,
            )
            .order_by(ChapterBaseQuestion.id)
        )
        questions = questions_result.scalars().all()
        total_questions = len(questions)

        # 获取用户在该章节的所有进度
        progress_result = await db.execute(
            select(MasteryExerciseProgress).where(
                and_(
                    MasteryExerciseProgress.user_id == user_id,
                    MasteryExerciseProgress.course_id == course_id,
                    MasteryExerciseProgress.chapter_id == chapter_id,
                )
            )
        )
        progress_list = progress_result.scalars().all()

        # 构建 question_id -> progress 的映射
        progress_map = {p.question_id: p for p in progress_list}

        # 构建每道题的进度信息
        progress_items = []
        for idx, question in enumerate(questions):
            progress = progress_map.get(question.id)
            if progress:
                progress_items.append(
                    MasteryExerciseProgressItem(
                        question_id=question.id,
                        question_index=idx,
                        question_type=progress.question_type or "base",
                        is_completed=progress.is_completed,
                        is_correct=progress.is_correct,
                        user_answer=progress.user_answer,
                        correct_answer=progress.correct_answer,
                        saved_code=progress.saved_code,
                        current_language=progress.current_language or "python",
                        attempt_count=progress.attempt_count,
                    )
                )
            else:
                progress_items.append(
                    MasteryExerciseProgressItem(
                        question_id=question.id,
                        question_index=idx,
                        question_type="base",
                        is_completed=False,
                        is_correct=False,
                    )
                )

        completed_questions = sum(1 for p in progress_items if p.is_completed)
        correct_questions = sum(1 for p in progress_items if p.is_correct)
        mastery_score = (
            (correct_questions / total_questions * 100) if total_questions > 0 else 0
        )

        return MasteryChapterDetailProgressResponse(
            chapter_id=chapter_id,
            total_questions=total_questions,
            completed_questions=completed_questions,
            correct_questions=correct_questions,
            mastery_score=mastery_score,
            is_passed=mastery_score >= 80,
            progress_items=progress_items,
        )


# 全局单例
mastery_progress_service = MasteryProgressService()
