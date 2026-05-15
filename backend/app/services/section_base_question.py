"""
Section Base Question Service - 小节基础测试题服务

提供：
1. 获取小节基础测试题
2. 提交答案并分析薄弱点
3. 生成个性化强化测试题

重构说明：
- 原名为 chapter_base_question，现已重构为 section_base_question
- 题目现在按小节组织，section_id 为必填字段
"""

from typing import Optional, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from collections import defaultdict

from app.models.section_base_question import SectionBaseQuestion
from app.models.section import Section
from app.models.chapter import Chapter
from app.services.ai import ai_service
from app.schemas.section_base_question import (
    BaseAnswersSubmitRequest,
    BaseAnswersSubmitResponse,
    BaseQuestionResult,
    EnhancedQuizGenerateRequest,
    EnhancedQuizGenerateResponse,
    EnhancedQuizQuestion,
    EnhancedQuizSubmitRequest,
    EnhancedQuizSubmitResponse,
)
class SectionBaseQuestionService:
    """小节基础测试题服务"""

    async def get_section_base_questions(
        self,
        db: AsyncSession,
        section_id: int,
        user_id: str = None,
    ) -> dict:
        """
        获取小节基础测试题（支持用户隔离）

        Args:
            db: 数据库会话
            section_id: 小节ID
            user_id: 用户ID（可选，用于过滤增强题）

        Returns:
            包含小节信息和基础题列表的字典

        Note:
            题目过滤逻辑：
            - 基础题（user_id=NULL）：所有用户共享
            - 强化题（user_id=指定）：仅生成用户可见
        """
        # 获取小节信息
        section_result = await db.execute(
            select(Section).where(Section.id == section_id)
        )
        section = section_result.scalar_one_or_none()
        if not section:
            return {
                "section_id": section_id,
                "section_title": "",
                "chapter_id": 0,
                "total_questions": 0,
                "questions": []
            }

        # 构建查询 - 用户隔离
        query = select(SectionBaseQuestion).where(
            SectionBaseQuestion.section_id == section_id,
            SectionBaseQuestion.is_active.is_(True)
        )
        if user_id:
            query = query.where(
                or_(
                    SectionBaseQuestion.user_id.is_(None),
                    SectionBaseQuestion.user_id == user_id
                )
            )
        else:
            query = query.where(SectionBaseQuestion.user_id.is_(None))
        query = query.order_by(SectionBaseQuestion.order_index)

        questions_result = await db.execute(query)
        questions = questions_result.scalars().all()

        return {
            "section_id": section_id,
            "section_title": section.title,
            "chapter_id": section.chapter_id,
            "total_questions": len(questions),
            "questions": [q.to_dict() for q in questions],
        }

    async def submit_base_answers(
        self,
        db: AsyncSession,
        section_id: int,
        request: BaseAnswersSubmitRequest,
        user_id: str = None,
    ) -> BaseAnswersSubmitResponse:
        """
        提交小节基础题答案并分析薄弱点

        Args:
            db: 数据库会话
            section_id: 小节ID
            request: 答案提交请求
            user_id: 用户ID（可选，用于更新 mastery_xp）

        Returns:
            包含结果分析和薄弱点识别的响应
        """
        from app.models.user import User

        # 获取小节信息
        section_result = await db.execute(
            select(Section).where(Section.id == section_id)
        )
        section_result.scalar_one_or_none()

        # 获取题目
        questions_result = await db.execute(
            select(SectionBaseQuestion)
            .where(SectionBaseQuestion.section_id == section_id, SectionBaseQuestion.is_active)
            .order_by(SectionBaseQuestion.order_index)
        )
        questions = questions_result.scalars().all()
        questions_map = {q.id: q for q in questions}

        # 计算结果
        # 使用字典统计每个知识点的正确/错误次数
        knowledge_point_stats = defaultdict(lambda: {"correct": 0, "wrong": 0})
        results = []
        correct_count = 0

        for answer_submit in request.answers:
            question = questions_map.get(answer_submit.question_id)
            if not question:
                continue

            is_correct = answer_submit.answer.strip().upper() == question.correct_answer.strip().upper()
            if is_correct:
                correct_count += 1
                # 统计知识点正确次数
                for kp in question.knowledge_points:
                    knowledge_point_stats[kp]["correct"] += 1
            else:
                # 统计知识点错误次数
                for kp in question.knowledge_points:
                    knowledge_point_stats[kp]["wrong"] += 1

            results.append(BaseQuestionResult(
                question_id=question.id,
                is_correct=is_correct,
                user_answer=answer_submit.answer,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                knowledge_points=question.knowledge_points,
            ))

        # 根据统计结果分类知识点
        # 薄弱点：错误次数 >= 正确次数（掌握度 <= 50%）
        # 已掌握：正确次数 > 错误次数 且 有正确记录
        weak_points = []
        strong_points = []

        for kp, stats in knowledge_point_stats.items():
            if stats["wrong"] >= stats["correct"]:
                # 错误次数 >= 正确次数，归类为薄弱点
                weak_points.append(kp)
            else:
                # 正确次数 > 错误次数，归类为已掌握
                strong_points.append(kp)

        # 更新用户精进之路经验值（如果提供了 user_id）
        xp_earned = 0
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[基础题] 提交结果: user_id={user_id}, correct_count={correct_count}")

        if user_id and correct_count > 0:
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            logger.info(f"[基础题] 查询用户: user={'存在' if user else '不存在'}")
            if user:
                from app.services.mastery_xp_transaction_service import MasteryXpTransactionService
                xp_earned = correct_count * 10  # 每题 10 XP
                logger.info(f"[基础题] 准备加经验: xp_earned={xp_earned}")
                mastery_xp_service = MasteryXpTransactionService(db)
                await mastery_xp_service.earn_xp(
                    user_id=user.id,
                    amount=xp_earned,
                    category="base_test",
                    reference_type="section",
                    reference_id=str(section_id),
                    description=f"小节基础测试答对 {correct_count} 题"
                )
                logger.info(f"[基础题] 经验已添加: xp_earned={xp_earned}")
        else:
            logger.info(f"[基础题] 跳过加经验: user_id={user_id}, correct_count={correct_count}")

        accuracy = correct_count / len(questions) if questions else 0

        return BaseAnswersSubmitResponse(
            section_id=section_id,
            total_questions=len(questions),
            correct_answers=correct_count,
            accuracy=accuracy,
            results=results,
            weak_points=weak_points,
            strong_points=strong_points,
            xp_earned=xp_earned,
        )

    async def generate_enhanced_quiz(
        self,
        db: AsyncSession,
        request: EnhancedQuizGenerateRequest,
        user_id: str,
        progress_callback: Optional[Callable[[int, dict, int, int], Awaitable[None]]] = None,
    ) -> EnhancedQuizGenerateResponse:
        """
        流式生成强化测试题 - 第一题立即可用，剩余异步生成

        Args:
            db: 数据库会话
            request: 生成请求（包含薄弱点）
            user_id: 用户ID
            progress_callback: 每生成一题的回调（用于WebSocket推送）

        Returns:
            包含第一题和会话ID，剩余题目在后台生成
        """
        import logging
        from app.services.exercise_generator import ExerciseGeneratorService

        logger = logging.getLogger(__name__)

        if not request.weak_points:
            return EnhancedQuizGenerateResponse(
                success=False,
                message="没有识别到薄弱点，无需生成强化题"
            )

        # 获取小节信息
        section_result = await db.execute(
            select(Section).where(Section.id == request.section_id)
        )
        section = section_result.scalar_one_or_none()
        if not section:
            return EnhancedQuizGenerateResponse(
                success=False,
                message="小节不存在"
            )

        # 获取课程/章节信息用于上下文
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == request.chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        chapter_title = chapter.title if chapter else f"章节 {request.chapter_id}"

        try:
            # 使用 ExerciseGeneratorService 实现流式生成
            generator = ExerciseGeneratorService(db)

            session_id, first_exercise, remaining_count = await generator.start_generation_session(
                user_id=user_id,
                session_type="enhanced",
                section_id=request.section_id,
                chapter_id=request.chapter_id,
                course_id=request.course_id,
                weak_points=request.weak_points,
                strong_points=request.strong_points or [],
                question_count=request.question_count or 3,
                section_title=section.title,
                chapter_title=chapter_title,
                progress_callback=progress_callback,
            )

            # 转换第一题为返回格式
            first_question = EnhancedQuizQuestion(
                id=str(first_exercise.get("id", "1")),
                type=first_exercise.get("type", "choice"),
                text=first_exercise.get("text", ""),
                options=first_exercise.get("options", []),
                correct_answer=first_exercise.get("correct_answer", ""),
                explanation=first_exercise.get("explanation", ""),
                knowledge_points=first_exercise.get("knowledge_points", []),
                difficulty=first_exercise.get("difficulty", 2),
            )

            # 保存第一题到 SectionBaseQuestion（让用户可以回顾）
            # 使用独立 session，避免失败时污染主事务
            from app.database import AsyncSessionLocal
            try:
                async with AsyncSessionLocal() as save_db:
                    max_order_result = await save_db.execute(
                        select(func.max(SectionBaseQuestion.order_index)).where(
                            SectionBaseQuestion.section_id == request.section_id,
                            SectionBaseQuestion.is_active,
                        )
                    )
                    max_order = max_order_result.scalar() or 0

                    db_question = SectionBaseQuestion(
                        section_id=request.section_id,
                        chapter_id=request.chapter_id,
                        user_id=user_id,
                        question_source='enhanced',
                        order_index=max_order + 1,
                        question_type=first_exercise.get("type", "choice"),
                        question_text=first_exercise.get("text", ""),
                        options=first_exercise.get("options", []),
                        correct_answer=first_exercise.get("correct_answer", ""),
                        explanation=first_exercise.get("explanation", ""),
                        knowledge_points=first_exercise.get("knowledge_points", []),
                        difficulty=first_exercise.get("difficulty", 2),
                        is_active=True,
                    )
                    save_db.add(db_question)
                    await save_db.commit()
            except Exception as e:
                logger.error(f"保存第一题到回顾表失败: {e}")

            logger.info(f"[强化题生成-流式] 第一题已生成, session_id={session_id[:8]}..., 剩余{remaining_count}题在后台生成")

            return EnhancedQuizGenerateResponse(
                success=True,
                session_id=session_id,
                questions=[first_question],  # 只返回第一题
                weak_points_addressed=request.weak_points,
                message=f"已生成第1题，剩余{remaining_count}题正在生成中..."
            )

        except ValueError as e:
            logger.error(f"[强化题生成-流式] 生成失败: {e}")
            return EnhancedQuizGenerateResponse(
                success=False,
                message=str(e)
            )
        except Exception as e:
            logger.error(f"[强化题生成-流式] 异常: {e}")
            return EnhancedQuizGenerateResponse(
                success=False,
                message=f"生成强化题失败: {str(e)}"
            )

    async def get_session_exercises(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> list[EnhancedQuizQuestion]:
        """
        获取会话已生成的所有题目

        用于前端轮询获取最新生成的题目
        """
        from app.services.exercise_generator import ExerciseGeneratorService

        generator = ExerciseGeneratorService(db)
        exercises = await generator.get_all_exercises(session_id)

        questions = []
        for ex in exercises:
            questions.append(EnhancedQuizQuestion(
                id=str(ex.get("id", "")),
                type=ex.get("type", "choice"),
                text=ex.get("text", ""),
                options=ex.get("options", []),
                correct_answer=ex.get("correct_answer", ""),
                explanation=ex.get("explanation", ""),
                knowledge_points=ex.get("knowledge_points", []),
                difficulty=ex.get("difficulty", 2),
            ))

        return questions

    async def submit_enhanced_quiz(
        self,
        db: AsyncSession,
        request: EnhancedQuizSubmitRequest,
        user_id: str,
    ) -> EnhancedQuizSubmitResponse:
        """
        提交强化测试题答案

        Args:
            db: 数据库会话
            request: 提交请求
            user_id: 用户ID

        Returns:
            包含结果和学习建议
        """
        from app.models.user import User
        from app.services.exercise_generator import ExerciseGeneratorService

        # 始终以数据库为唯一真实来源（后台异步生成的题目不在内存中）
        generator = ExerciseGeneratorService(db)
        db_session = await generator.get_session(request.session_id)

        if not db_session:
            return EnhancedQuizSubmitResponse(
                success=False,
                session_id=request.session_id,
                section_id=request.section_id,
                total_questions=0,
                correct_answers=0,
                accuracy=0,
                message="会话不存在或已过期"
            )

        questions = db_session.generated_exercises

        # 计算结果
        results = []
        correct_count = 0

        for answer in request.answers:
            question = next(
                (q for q in questions if str(q.get("id", "")) == str(answer.get("question_id", ""))),
                None
            )
            if question:
                is_correct = answer.get("answer", "").strip().upper() == str(question.get("correct_answer", "")).strip().upper()
                if is_correct:
                    correct_count += 1
                results.append({
                    "question_id": answer.get("question_id"),
                    "is_correct": is_correct,
                    "user_answer": answer.get("answer"),
                    "correct_answer": question.get("correct_answer"),
                })

        accuracy = correct_count / len(questions) if questions else 0
        passed = accuracy >= 0.8

        # 更新用户精进之路经验值
        xp_earned = 0
        if correct_count > 0:
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                from app.services.mastery_xp_transaction_service import MasteryXpTransactionService
                xp_earned = correct_count * 15  # 强化题每题 15 XP
                mastery_xp_service = MasteryXpTransactionService(db)
                await mastery_xp_service.earn_xp(
                    user_id=user.id,
                    amount=xp_earned,
                    category="enhanced_test",
                    reference_type="section",
                    reference_id=str(request.section_id),
                    description=f"强化测试答对 {correct_count} 题"
                )

        # 生成学习建议
        recommendations = []
        if not passed:
            recommendations.append("建议回顾相关知识点后再次练习")
        if accuracy < 0.5:
            recommendations.append("基础掌握较弱，建议重新学习小节内容")

        return EnhancedQuizSubmitResponse(
            success=True,
            session_id=request.session_id,
            section_id=request.section_id,
            total_questions=len(questions),
            correct_answers=correct_count,
            accuracy=accuracy,
            xp_earned=xp_earned,
            mastery_points_earned=correct_count * 5 if passed else 0,
            results=results,
            recommendations=recommendations,
            passed=passed,
            message="强化测试完成"
        )


# 单例
section_base_question_service = SectionBaseQuestionService()

# 向后兼容的别名
chapter_base_question_service = section_base_question_service
