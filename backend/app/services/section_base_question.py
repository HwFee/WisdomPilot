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
    PersistEnhancedQuestionRequest,
    PersistEnhancedQuestionResponse,
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

        # 根据 BKT 掌握度分类知识点
        # 优先使用 BKT 掌握概率（p_l），阈值 0.80
        # 如果 BKT 数据不存在（首次做题），按简单统计兜底
        weak_points = []
        strong_points = []

        if user_id:
            from app.models.knowledge_point_mastery import KnowledgePointMastery, MASTERY_THRESHOLD
            all_kp_names = list(knowledge_point_stats.keys())
            if all_kp_names:
                kp_result = await db.execute(
                    select(KnowledgePointMastery).where(
                        KnowledgePointMastery.user_id == user_id,
                        KnowledgePointMastery.knowledge_point.in_(all_kp_names),
                    )
                )
                kp_masteries = kp_result.scalars().all()
                kp_mastery_map = {m.knowledge_point: m for m in kp_masteries}
            else:
                kp_mastery_map = {}

            for kp, stats in knowledge_point_stats.items():
                kp_mastery = kp_mastery_map.get(kp)
                if kp_mastery and kp_mastery.total_attempts > 0:
                    # 有 BKT 数据，用 p_l 判断掌握状态
                    if kp_mastery.p_l >= MASTERY_THRESHOLD:
                        strong_points.append(kp)
                    else:
                        weak_points.append(kp)
                else:
                    # 无 BKT 数据（首次），按简单统计兜底
                    if stats["wrong"] >= stats["correct"]:
                        weak_points.append(kp)
                    else:
                        strong_points.append(kp)
        else:
            for kp, stats in knowledge_point_stats.items():
                if stats["wrong"] >= stats["correct"]:
                    weak_points.append(kp)
                else:
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

            # 后台会并发生成所有题目，每道题在写入 ExerciseGenerationSession 前
            # 会先保存到 SectionBaseQuestion（获得真实数据库ID并更新 exercise.id）
            session_id, first_exercise, remaining_count = await generator.generate_first_then_stream(
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

            # 转换第一题为返回格式（此时 first_exercise 已被后台更新为真实数据库ID）
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
        import logging
        from app.models.user import User
        from app.services.exercise_generator import ExerciseGeneratorService

        logger = logging.getLogger(__name__)

        try:
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

            questions = db_session.generated_exercises or []

            # 计算结果
            results = []
            correct_count = 0

            for idx, answer in enumerate(request.answers):
                answer_qid = str(answer.get("question_id", ""))

                # 主路径：按 id 精确匹配（持久化后 id 已是真实数据库ID）
                question = next(
                    (q for q in questions if str(q.get("id", "")) == answer_qid),
                    None
                )

                # 兜底 1：前端发来的还是 "temp_N"，按 N 取位置
                if not question and answer_qid.startswith("temp_"):
                    try:
                        temp_idx = int(answer_qid.replace("temp_", ""))
                        if 0 <= temp_idx < len(questions):
                            question = questions[temp_idx]
                    except ValueError:
                        pass

                # 兜底 2：前端发来的是真实ID，但session里还是 temp_N（JSON更新没落库的旧bug）
                # 用 answer 在 request.answers 中的位置直接对应 questions 同位置
                if not question and idx < len(questions):
                    question = questions[idx]
                    logger.warning(
                        f"[submit_enhanced_quiz] answer id={answer_qid} 无法精确匹配, "
                        f"按位置{idx}兜底匹配到 question id={question.get('id')}"
                    )

                if question:
                    is_correct = answer.get("answer", "").strip().upper() == str(question.get("correct_answer", "")).strip().upper()
                    if is_correct:
                        correct_count += 1
                    results.append({
                        "question_id": question.get("id") or answer.get("question_id"),
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
                    try:
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
                    except Exception as xp_err:
                        # 经验发放失败不应让整个提交失败
                        logger.error(f"[submit_enhanced_quiz] 经验发放失败: {xp_err}")
                        xp_earned = 0

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

        except Exception as e:
            import traceback
            try:
                await db.rollback()
            except Exception as rb_err:
                logger.error(f"[submit_enhanced_quiz] rollback 失败: {rb_err}")
            logger.error(f"[submit_enhanced_quiz] 提交失败: {e}\n{traceback.format_exc()}")
            return EnhancedQuizSubmitResponse(
                success=False,
                session_id=request.session_id,
                section_id=request.section_id,
                total_questions=0,
                correct_answers=0,
                accuracy=0,
                xp_earned=0,
                mastery_points_earned=0,
                results=[],
                recommendations=[],
                passed=False,
                message=f"提交失败: {type(e).__name__}: {str(e)}"
            )

    async def persist_enhanced_question(
        self,
        db: AsyncSession,
        user_id: str,
        request: PersistEnhancedQuestionRequest,
    ) -> PersistEnhancedQuestionResponse:
        """将 ExerciseGenerationSession 中的单道强化题持久化到 SectionBaseQuestion

        用户做题提交时调用，获得真实数据库ID用于进度保存和错题本跳转。
        """
        import logging
        from app.services.exercise_generator import ExerciseGeneratorService
        from sqlalchemy import func
        import traceback

        logger = logging.getLogger(__name__)

        # >>> DEBUG MARKER: 确认新代码已加载 <<<
        print(f"\n[PERSIST_DEBUG] === persist_enhanced_question called === "
              f"session={request.session_id[:8] if request.session_id else 'NONE'} "
              f"index={request.question_index} section={request.section_id}", flush=True)

        try:
            # 1. 获取生成会话
            generator = ExerciseGeneratorService(db)
            session = await generator.get_session(request.session_id)

            if not session:
                return PersistEnhancedQuestionResponse(
                    success=False,
                    message="会话不存在或已过期"
                )

            if session.user_id != user_id:
                return PersistEnhancedQuestionResponse(
                    success=False,
                    message="无权访问该会话"
                )

            exercises_list = session.generated_exercises or []
            if not exercises_list:
                return PersistEnhancedQuestionResponse(
                    success=False,
                    message="会话尚未生成任何题目"
                )

            # 2. 查找指定索引的题目
            # 优先按 exercise 的 id 中的索引匹配（如 "temp_0" -> 0, "temp_1" -> 1）
            # 其次按 generated_exercises 列表的位置索引匹配
            exercise = None

            # 第一轮：按 id 中的 temp_N 索引精确匹配
            for ex in exercises_list:
                ex_id = str(ex.get("id", ""))
                if ex_id.startswith("temp_"):
                    try:
                        temp_idx = int(ex_id.replace("temp_", ""))
                        if temp_idx == request.question_index:
                            exercise = ex
                            break
                    except ValueError:
                        pass

            # 第二轮：按列表位置索引匹配
            if not exercise and 0 <= request.question_index < len(exercises_list):
                exercise = exercises_list[request.question_index]

            if not exercise:
                return PersistEnhancedQuestionResponse(
                    success=False,
                    message=f"会话中未找到索引为 {request.question_index} 的题目"
                )

            # 3. 检查是否已持久化（避免重复保存）
            # 通过 session_id + question_index 无法直接查，但可以通过 exercise 的 id 判断
            # 如果 id 已经是数字（真实ID），说明已持久化
            existing_id = exercise.get("id", "")
            if existing_id and not str(existing_id).startswith("temp_"):
                try:
                    return PersistEnhancedQuestionResponse(
                        success=True,
                        question_id=int(existing_id),
                        message="题目已持久化"
                    )
                except (ValueError, TypeError):
                    pass

            # 4. 保存到 SectionBaseQuestion（查 max order_index + 1）
            #    查当前用户的所有 active 记录（基础题 + 自己的强化题），
            #    只排除其他用户的强化题。新强化题接在自己已有题后面，
            #    避免覆盖之前生成的。
            max_order_result = await db.execute(
                select(func.max(SectionBaseQuestion.order_index)).where(
                    SectionBaseQuestion.section_id == request.section_id,
                    SectionBaseQuestion.is_active.is_(True),
                    or_(
                        SectionBaseQuestion.user_id.is_(None),    # 基础题
                        SectionBaseQuestion.user_id == user_id,   # 自己的强化题
                    ),
                )
            )
            max_order = max_order_result.scalar() or 0

            db_question = SectionBaseQuestion(
                section_id=request.section_id,
                chapter_id=request.chapter_id,
                user_id=user_id,
                question_source='enhanced',
                order_index=max_order + 1,
                question_type=exercise.get("type", "choice"),
                question_text=exercise.get("text", ""),
                options=exercise.get("options", []),
                correct_answer=exercise.get("correct_answer", ""),
                explanation=exercise.get("explanation", ""),
                knowledge_points=exercise.get("knowledge_points", []),
                difficulty=exercise.get("difficulty", 2),
                is_active=True,
            )
            db.add(db_question)
            # flush 拿到 db_question.id，但不提交，让 session.generated_exercises 的修改
            # 在同一事务中一并提交（避免中间 commit 导致 session 属性被 expire 后丢失修改）
            await db.flush()

            persisted_id = db_question.id

            # 5. 更新 ExerciseGenerationSession 中的题目ID（避免重复保存 + 让 submit 能按真实ID匹配）
            #    JSON 列默认不检测列表内部就地变更，必须**重新赋值整个列表**才会触发持久化
            new_exercises = list(exercises_list)
            target_old_id = str(exercise.get("id", ""))
            for i, ex in enumerate(new_exercises):
                if str(ex.get("id", "")) == target_old_id:
                    new_exercises[i] = {**ex, "id": str(persisted_id)}
                    break
            session.generated_exercises = new_exercises

            await db.commit()

            logger.info(
                f"[persist_enhanced_question] 题目已持久化: "
                f"session={request.session_id[:8]}..., index={request.question_index}, db_id={persisted_id}"
            )

            return PersistEnhancedQuestionResponse(
                success=True,
                question_id=persisted_id,
                message="题目已持久化"
            )

        except Exception as e:
            # 一旦抛异常，事务必须回滚，否则后续请求复用同一 session 会一直报错
            print(f"\n[PERSIST_DEBUG] !!! EXCEPTION caught: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
            try:
                await db.rollback()
            except Exception as rb_err:
                print(f"[PERSIST_DEBUG] rollback 失败: {rb_err}", flush=True)
                logger.error(f"[persist_enhanced_question] rollback 失败: {rb_err}")
            logger.error(
                f"[persist_enhanced_question] 持久化失败: {e}\n{traceback.format_exc()}"
            )
            return PersistEnhancedQuestionResponse(
                success=False,
                question_id=0,
                message=f"持久化失败: {type(e).__name__}: {str(e)}"
            )


# 单例
section_base_question_service = SectionBaseQuestionService()

# 向后兼容的别名
chapter_base_question_service = section_base_question_service
