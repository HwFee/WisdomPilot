"""
Chapter Base Question Service - 章节基础测试题服务

提供：
1. 获取章节基础测试题
2. 提交答案并分析薄弱点
3. 生成个性化强化测试题
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from collections import defaultdict

from app.models.chapter_base_question import ChapterBaseQuestion
from app.models.chapter import Chapter
from app.models.chapter_mastery import ChapterMastery
from app.services.ai import ai_service
from app.schemas.chapter_base_question import (
    BaseQuestionResponse,
    BaseAnswersSubmitRequest,
    BaseAnswersSubmitResponse,
    BaseQuestionResult,
    EnhancedQuizGenerateRequest,
    EnhancedQuizGenerateResponse,
    EnhancedQuizQuestion,
    EnhancedQuizSubmitRequest,
    EnhancedQuizSubmitResponse,
)
from app.utils.time import utc_now


class EnhancedQuizSession:
    """强化测试会话（内存存储）"""
    def __init__(
        self,
        session_id: str,
        user_id: str,
        chapter_id: int,
        course_id: int,
        questions: List[dict],
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.chapter_id = chapter_id
        self.course_id = course_id
        self.questions = questions
        self.created_at = utc_now()


class ChapterBaseQuestionService:
    """章节基础测试题服务"""

    # 内存中的强化测试会话
    _enhanced_sessions: dict[str, EnhancedQuizSession] = {}

    async def get_chapter_base_questions(
        self,
        db: AsyncSession,
        chapter_id: int,
    ) -> dict:
        """
        获取章节基础测试题

        Args:
            db: 数据库会话
            chapter_id: 章节ID

        Returns:
            包含章节信息和基础题列表的字典
        """
        # 获取章节信息
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        if not chapter:
            return {"chapter_id": chapter_id, "chapter_title": "", "total_questions": 0, "questions": []}

        # 获取基础题
        questions_result = await db.execute(
            select(ChapterBaseQuestion)
            .where(ChapterBaseQuestion.chapter_id == chapter_id, ChapterBaseQuestion.is_active == True)
            .order_by(ChapterBaseQuestion.order_index)
        )
        questions = questions_result.scalars().all()

        return {
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "total_questions": len(questions),
            "questions": [q.to_dict() for q in questions],
        }

    async def submit_base_answers(
        self,
        db: AsyncSession,
        chapter_id: int,
        request: BaseAnswersSubmitRequest,
        user_id: str = None,
    ) -> BaseAnswersSubmitResponse:
        """
        提交基础题答案并分析薄弱点

        Args:
            db: 数据库会话
            chapter_id: 章节ID
            request: 答案提交请求
            user_id: 用户ID（可选，用于更新 mastery_xp）

        Returns:
            包含结果分析和薄弱点识别的响应
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[submit_base_answers] 开始处理 chapter_id={chapter_id}, user_id={user_id}, answers_count={len(request.answers)}")

        from app.models.user import User
        from app.services.profile import profile_service

        # 获取题目
        questions_result = await db.execute(
            select(ChapterBaseQuestion)
            .where(ChapterBaseQuestion.chapter_id == chapter_id, ChapterBaseQuestion.is_active == True)
            .order_by(ChapterBaseQuestion.order_index)
        )
        questions = {q.id: q for q in questions_result.scalars().all()}
        logger.info(f"[submit_base_answers] 获取到 {len(questions)} 道题目")

        results = []
        correct_count = 0

        # 统计知识点正确率
        knowledge_stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})

        for answer in request.answers:
            question = questions.get(answer.question_id)
            if not question:
                continue

            # 判断答案是否正确
            is_correct = str(answer.answer).strip().upper() == str(question.correct_answer).strip().upper()

            if is_correct:
                correct_count += 1

            # 统计知识点
            for kp in question.knowledge_points or []:
                knowledge_stats[kp]["total"] += 1
                if is_correct:
                    knowledge_stats[kp]["correct"] += 1

            results.append(BaseQuestionResult(
                question_id=answer.question_id,
                is_correct=is_correct,
                user_answer=answer.answer,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                knowledge_points=question.knowledge_points or [],
            ))

        total_questions = len(questions)
        accuracy = correct_count / total_questions if total_questions > 0 else 0

        logger.info(f"[submit_base_answers] 答题结果: correct_count={correct_count}, total={total_questions}, accuracy={accuracy:.2%}")

        # 识别薄弱点和强项
        weak_points = []
        strong_points = []

        for kp, stats in knowledge_stats.items():
            kp_accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if kp_accuracy < 0.5:
                weak_points.append(kp)
            elif kp_accuracy >= 0.8:
                strong_points.append(kp)

        # 更新用户 mastery_xp（基础测试：根据正确率计算 XP）
        # 注：智核已在每道题答对时通过 mastery_progress.save_exercise_progress 发放
        # 此处不再批量发放智核
        if user_id:
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                base_xp = int(accuracy * 20)  # 基础测试最高 20 XP
                await profile_service.add_mastery_xp(db, user, base_xp)
                logger.info(f"[submit_base_answers] 更新用户 {user_id[:8]}... mastery_xp +{base_xp}")

        logger.info(f"[submit_base_answers] 返回结果: 不发放智核（已通过每题保存时发放）")

        return BaseAnswersSubmitResponse(
            total_questions=total_questions,
            correct_answers=correct_count,
            accuracy=accuracy,
            results=results,
            weak_points=weak_points,
            strong_points=strong_points,
        )

    async def generate_enhanced_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: EnhancedQuizGenerateRequest,
    ) -> EnhancedQuizGenerateResponse:
        """
        生成个性化强化测试题，并持久化到数据库

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 生成请求

        Returns:
            包含强化测试题的响应
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[generate_enhanced_quiz] 开始: user={user_id[:8]}..., chapter={request.chapter_id}, weak_points={request.weak_points}, count={request.question_count}")

        from app.models.mastery_exercise_progress import MasteryExerciseProgress

        # 获取章节信息
        logger.info(f"[generate_enhanced_quiz] 步骤1: 获取章节信息...")
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == request.chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        if not chapter:
            logger.error(f"[generate_enhanced_quiz] 章节不存在: chapter_id={request.chapter_id}")
            return EnhancedQuizGenerateResponse(
                success=False,
                message="章节不存在",
            )
        logger.info(f"[generate_enhanced_quiz] 章节信息获取成功: {chapter.title}")

        # 使用 AI 生成强化题
        logger.info(f"[generate_enhanced_quiz] 步骤2: 调用AI生成题目...")
        questions = await self._generate_enhanced_questions_with_ai(
            chapter=chapter,
            weak_points=request.weak_points,
            question_count=request.question_count,
            question_types=request.question_types,
        )
        logger.info(f"[generate_enhanced_quiz] AI生成完成, 获得 {len(questions)} 道题目")

        if not questions:
            logger.error(f"[generate_enhanced_quiz] AI未返回任何题目")
            return EnhancedQuizGenerateResponse(
                success=False,
                message="AI 服务暂时不可用，请稍后重试",
            )

        # 获取当前章节题目的最大 order_index
        logger.info(f"[generate_enhanced_quiz] 步骤3: 获取最大order_index...")

        # 先查询该章节当前有多少题目
        count_result = await db.execute(
            select(ChapterBaseQuestion.id)
            .where(ChapterBaseQuestion.chapter_id == request.chapter_id)
        )
        existing_ids = count_result.scalars().all()
        logger.info(f"[generate_enhanced_quiz] 章节当前已有题目数: {len(existing_ids)}, 题目IDs: {existing_ids}")

        max_order_result = await db.execute(
            select(ChapterBaseQuestion.order_index)
            .where(ChapterBaseQuestion.chapter_id == request.chapter_id)
            .order_by(ChapterBaseQuestion.order_index.desc())
            .limit(1)
        )
        max_order_row = max_order_result.scalar()
        logger.info(f"[generate_enhanced_quiz] 查询结果 max_order_row={max_order_row}, 类型={type(max_order_row)}")

        # 确保 max_order 是整数且不为 None
        if max_order_row is None:
            max_order = 0
            logger.warning(f"[generate_enhanced_quiz] max_order 为 None，设置为 0")
        else:
            max_order = int(max_order_row)
        logger.info(f"[generate_enhanced_quiz] 最终 max_order={max_order}, 新题目将从 order_index={max_order + 1} 开始")

        # 持久化题目到数据库，并创建进度记录（未完成状态）
        logger.info(f"[generate_enhanced_quiz] 步骤4: 持久化题目到数据库...")
        db_questions = []
        for i, q in enumerate(questions):
            logger.info(f"[generate_enhanced_quiz] 创建题目 {i+1}: type={q.type}, text={q.text[:30]}...")
            db_question = ChapterBaseQuestion(
                chapter_id=request.chapter_id,
                question_source="精进之路",
                order_index=max_order + i + 1,
                question_type=q.type,
                question_text=q.text,
                options=q.options,
                correct_answer=q.correct_answer if hasattr(q, 'correct_answer') else "",
                explanation=q.explanation if hasattr(q, 'explanation') else None,
                knowledge_points=q.knowledge_points,
                difficulty=q.difficulty,
                code_template=q.code_template if hasattr(q, 'code_template') else None,
                test_cases=q.test_cases if hasattr(q, 'test_cases') else None,
            )
            db.add(db_question)
            db_questions.append(db_question)

        logger.info(f"[generate_enhanced_quiz] 步骤5: 提交题目到数据库...")
        await db.commit()
        logger.info(f"[generate_enhanced_quiz] 题目已提交到数据库")

        # 刷新获取生成的ID
        logger.info(f"[generate_enhanced_quiz] 步骤6: 刷新获取ID...")
        for q in db_questions:
            await db.refresh(q)
        logger.info(f"[generate_enhanced_quiz] ID刷新完成, 题目IDs: {[q.id for q in db_questions]}")
        # 详细记录每道题的 ID 和 order_index 对应关系
        for i, db_q in enumerate(db_questions):
            logger.info(f"[generate_enhanced_quiz] 题目{i+1}: 数据库ID={db_q.id}, order_index={db_q.order_index}, chapter_id={db_q.chapter_id}")

        # 为每道题创建进度记录（未完成状态），方便错题本跳转
        logger.info(f"[generate_enhanced_quiz] 步骤7: 创建进度记录...")
        for db_q in db_questions:
            progress = MasteryExerciseProgress(
                user_id=user_id,
                course_id=request.course_id,
                chapter_id=request.chapter_id,
                question_id=db_q.id,
                is_completed=False,
                is_correct=False,
            )
            db.add(progress)

        await db.commit()
        logger.info(f"[generate_enhanced_quiz] 进度记录创建完成")

        # 构建返回的题目列表（带数据库ID）
        logger.info(f"[generate_enhanced_quiz] 步骤8: 构建返回数据...")
        persisted_questions = []
        for db_q, q in zip(db_questions, questions):
            persisted_questions.append(EnhancedQuizQuestion(
                id=str(db_q.id),  # 使用数据库ID
                type=db_q.question_type,
                difficulty=db_q.difficulty,
                text=db_q.question_text,
                options=db_q.options,
                correct_answer=db_q.correct_answer,
                explanation=db_q.explanation,
                knowledge_points=db_q.knowledge_points,
                code_template=db_q.code_template,
                test_cases=db_q.test_cases,
            ))

        # 创建会话（用于提交时的验证）
        session_id = str(uuid.uuid4())
        logger.info(f"[generate_enhanced_quiz] 步骤9: 创建会话 session_id={session_id}")
        self._enhanced_sessions[session_id] = EnhancedQuizSession(
            session_id=session_id,
            user_id=user_id,
            chapter_id=request.chapter_id,
            course_id=request.course_id,
            questions=[q.model_dump() for q in persisted_questions],
        )

        logger.info(f"[generate_enhanced_quiz] 完成! session_id={session_id}, questions_count={len(persisted_questions)}")
        return EnhancedQuizGenerateResponse(
            success=True,
            session_id=session_id,
            questions=persisted_questions,
            weak_points_addressed=request.weak_points,
            message=f"成功生成 {len(persisted_questions)} 道强化测试题",
        )

    async def submit_enhanced_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: EnhancedQuizSubmitRequest,
    ) -> EnhancedQuizSubmitResponse:
        """
        提交强化测试题答案

        不再依赖内存会话，而是从数据库读取题目信息。
        进度已经在每道题答完后保存，这里主要用于：
        1. 计算最终结果
        2. 更新 XP
        3. 生成建议

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 提交请求

        Returns:
            测试结果
        """
        from app.models.user import User
        from app.services.profile import profile_service
        from app.models.mastery_exercise_progress import MasteryExerciseProgress

        # 从答案中提取 question_id 列表
        question_ids = []
        for answer in request.answers:
            qid = answer.get("question_id")
            if qid:
                try:
                    question_ids.append(int(qid))
                except (ValueError, TypeError):
                    continue

        if not question_ids:
            return EnhancedQuizSubmitResponse(
                success=False,
                session_id=request.session_id,
                total_questions=0,
                correct_answers=0,
                accuracy=0,
                message="没有有效的答案",
            )

        # 从数据库获取题目信息
        questions_result = await db.execute(
            select(ChapterBaseQuestion).where(
                ChapterBaseQuestion.id.in_(question_ids)
            )
        )
        questions = questions_result.scalars().all()
        questions_map = {q.id: q for q in questions}

        # 获取用户对这些题目的进度（用于获取 chapter_id 和 course_id）
        progress_result = await db.execute(
            select(MasteryExerciseProgress).where(
                MasteryExerciseProgress.user_id == user_id,
                MasteryExerciseProgress.question_id.in_(question_ids),
            )
        )
        progresses = progress_result.scalars().all()

        # 确定 chapter_id 和 course_id
        chapter_id = None
        course_id = None
        if progresses:
            chapter_id = progresses[0].chapter_id
            course_id = progresses[0].course_id

        # 评估答案
        results = []
        correct_count = 0

        for answer in request.answers:
            question_id = answer.get("question_id")
            user_answer = answer.get("answer", "")

            try:
                qid_int = int(question_id)
            except (ValueError, TypeError):
                continue

            question = questions_map.get(qid_int)
            if not question:
                continue

            # 获取正确答案
            correct_answer = question.correct_answer or ""
            is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()

            if is_correct:
                correct_count += 1

            results.append({
                "question_id": str(question_id),
                "is_correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "explanation": question.explanation or "",
                "knowledge_points": question.knowledge_points or [],
            })

        total_questions = len(question_ids)
        accuracy = correct_count / total_questions if total_questions > 0 else 0
        xp_earned = int(accuracy * 30)
        mastery_points_earned = int(accuracy * 15)

        # 更新用户 mastery_xp
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            await profile_service.add_mastery_xp(db, user, xp_earned)
            # 注：智核已在每道题答对时立即发放，此处不再批量发放

        # 进度已经在每道题答完后保存了，这里不需要再更新

        # 更新用户章节掌握度
        if chapter_id and course_id:
            await self._update_user_progress(
                db=db,
                user_id=user_id,
                chapter_id=chapter_id,
                correct_count=correct_count,
                total_count=total_questions,
                course_id=course_id,
            )

        # 清理会话（如果存在）
        self._enhanced_sessions.pop(request.session_id, None)

        return EnhancedQuizSubmitResponse(
            success=True,
            session_id=request.session_id,
            total_questions=total_questions,
            correct_answers=correct_count,
            accuracy=accuracy,
            xp_earned=xp_earned,
            mastery_points_earned=mastery_points_earned,
            results=results,
            recommendations=self._generate_recommendations(accuracy, results),
            passed=accuracy >= 0.8,
            message="提交成功" + ("，恭喜通过！" if accuracy >= 0.8 else ""),
        )

    async def _generate_enhanced_questions_with_ai(
        self,
        chapter: Chapter,
        weak_points: List[str],
        question_count: int,
        question_types: List[str],
    ) -> List[EnhancedQuizQuestion]:
        """使用 AI 生成强化测试题 (优先使用 MiniMax)"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[_generate_enhanced_questions_with_ai] 开始生成题目: chapter={chapter.title}, weak_points={weak_points}, count={question_count}")

        # 优先使用 MiniMax provider，否则使用主 AI provider
        provider = None
        if ai_service.is_minimax_configured():
            provider = ai_service.minimax_provider
            logger.info(f"[_generate_enhanced_questions_with_ai] 使用 MiniMax provider")
        elif ai_service.is_configured():
            provider = ai_service.provider
            logger.info(f"[_generate_enhanced_questions_with_ai] 使用主 AI provider")
        else:
            logger.warning(f"[_generate_enhanced_questions_with_ai] 没有可用的 AI provider")

        if provider is None:
            logger.error(f"[_generate_enhanced_questions_with_ai] provider 为空，返回空列表")
            return []

        # 构建提示
        weak_points_str = "、".join(weak_points) if weak_points else "基础知识"
        type_str = "、".join(question_types)

        prompt = f"""你是一位专业的编程测试题出题老师。请根据以下信息生成 {question_count} 道强化测试题：

章节标题：{chapter.title}
章节描述：{chapter.description or '无'}
需要强化的知识点：{weak_points_str}
题目类型：{type_str}

请以 JSON 数组格式返回，格式如下：
```json
[
  {{
    "id": "eq_001",
    "type": "choice",
    "difficulty": 2,
    "text": "题目描述",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "B",
    "explanation": "答案解析",
    "knowledge_points": ["知识点1"]
  }},
  {{
    "id": "eq_002",
    "type": "programming",
    "difficulty": 2,
    "text": "编程题目描述",
    "code_template": "代码模板",
    "test_cases": [{{"input": "输入", "expected": "期望输出"}}],
    "correct_answer": "参考代码",
    "explanation": "解题思路",
    "knowledge_points": ["知识点"]
  }}
]
```

要求：
1. 题目难度适中（2-3）
2. 重点考查薄弱知识点
3. 选择题要有 4 个选项
4. 编程题要有代码模板和测试用例
"""

        try:
            # 调用 AI 服务
            logger.info(f"[_generate_enhanced_questions_with_ai] 调用 AI provider.generate_explanation...")
            response = await provider.generate_explanation(prompt)
            logger.info(f"[_generate_enhanced_questions_with_ai] AI 返回响应, 长度: {len(response) if response else 0}")
            logger.debug(f"[_generate_enhanced_questions_with_ai] AI 响应内容: {response[:500] if response else 'None'}...")

            # 解析 JSON
            import json
            import re

            # 提取 JSON 数组
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
                logger.info(f"[_generate_enhanced_questions_with_ai] 从 markdown 代码块提取 JSON")
            else:
                json_str = response
                logger.info(f"[_generate_enhanced_questions_with_ai] 直接使用响应作为 JSON")

            questions_data = json.loads(json_str)
            logger.info(f"[_generate_enhanced_questions_with_ai] JSON 解析成功, 题目数量: {len(questions_data)}")

            result = [
                EnhancedQuizQuestion(
                    id=q.get("id", f"eq_{i}"),
                    type=q.get("type", "choice"),
                    difficulty=q.get("difficulty", 2),
                    text=q.get("text", ""),
                    options=q.get("options"),
                    correct_answer=q.get("correct_answer", ""),
                    explanation=q.get("explanation"),
                    code_template=q.get("code_template"),
                    test_cases=q.get("test_cases"),
                    knowledge_points=q.get("knowledge_points", []),
                )
                for i, q in enumerate(questions_data)
            ]
            logger.info(f"[_generate_enhanced_questions_with_ai] 题目构建完成, 返回 {len(result)} 道题")
            return result
        except Exception as e:
            import logging
            logging.error(f"[_generate_enhanced_questions_with_ai] AI 生成题目失败: {e}")
            import traceback
            logging.error(f"[_generate_enhanced_questions_with_ai] 异常堆栈:\n{traceback.format_exc()}")
            return []

    async def _update_user_progress(
        self,
        db: AsyncSession,
        user_id: str,
        chapter_id: int,
        correct_count: int,
        total_count: int,
        course_id: int = 0,
    ) -> None:
        """更新用户进度"""
        result = await db.execute(
            select(ChapterMastery).where(
                and_(
                    ChapterMastery.user_id == user_id,
                    ChapterMastery.chapter_id == chapter_id,
                )
            )
        )
        mastery = result.scalar_one_or_none()

        accuracy = correct_count / total_count if total_count > 0 else 0

        if mastery:
            mastery.total_exercises += total_count
            mastery.correct_exercises += correct_count
            mastery.accuracy_score = (mastery.correct_exercises / mastery.total_exercises * 100) if mastery.total_exercises > 0 else 0
            mastery.mastery_score = min(100, mastery.mastery_score + (accuracy * 5))
        else:
            mastery = ChapterMastery(
                user_id=user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                total_exercises=total_count,
                correct_exercises=correct_count,
                accuracy_score=accuracy * 100,
                mastery_score=min(100, accuracy * 30),
                mastery_level="入门",
            )
            db.add(mastery)

        await db.commit()

    def _generate_recommendations(self, accuracy: float, results: List[dict]) -> List[str]:
        """生成学习建议"""
        recommendations = []

        if accuracy >= 0.9:
            recommendations.append("表现优秀！可以继续下一章节的学习。")
        elif accuracy >= 0.7:
            recommendations.append("掌握良好，建议复习错误的知识点。")
        else:
            recommendations.append("建议重新学习相关知识点后再进行测试。")

        # 分析错误的知识点
        wrong_topics = []
        for r in results:
            if not r.get("is_correct"):
                wrong_topics.extend(r.get("knowledge_points", []))

        if wrong_topics:
            unique_topics = list(set(wrong_topics))[:3]
            recommendations.append(f"重点复习：{', '.join(unique_topics)}")

        return recommendations


# 全局单例
chapter_base_question_service = ChapterBaseQuestionService()
