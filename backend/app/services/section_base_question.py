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

import uuid
from typing import List
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
from app.utils.time import utc_now


class EnhancedQuizSession:
    """强化测试会话（内存存储）"""
    def __init__(
        self,
        session_id: str,
        user_id: str,
        section_id: int,
        chapter_id: int,
        course_id: int,
        questions: List[dict],
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.section_id = section_id
        self.chapter_id = chapter_id
        self.course_id = course_id
        self.questions = questions
        self.created_at = utc_now()


class SectionBaseQuestionService:
    """小节基础测试题服务"""

    # 内存中的强化测试会话
    _enhanced_sessions: dict[str, EnhancedQuizSession] = {}

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
    ) -> EnhancedQuizGenerateResponse:
        """
        根据薄弱点生成强化测试题，并持久化到数据库

        Args:
            db: 数据库会话
            request: 生成请求（包含薄弱点）
            user_id: 用户ID

        Returns:
            包含 AI 生成的强化测试题

        存储方案：
        - 强化题存储到 section_base_questions 表
        - question_source = 'enhanced'
        - user_id = 生成用户ID（用户隔离）
        - 这样错题本可以统一查看基础题和强化题
        """
        import json
        import re
        import logging
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

        # 使用 AI 生成强化题
        try:
            prompt = f"""你是一个专业的编程教育题目出题专家。请根据以下薄弱知识点，生成 {request.question_count} 道强化练习题。

课程: C语言程序设计
章节: {chapter_title}
小节: {section.title}
薄弱知识点: {', '.join(request.weak_points)}
已掌握知识点: {', '.join(request.strong_points) if request.strong_points else '无'}

要求：
1. 题目要针对薄弱知识点进行强化训练
2. 难度适中，循序渐进
3. 提供清晰的解析

请严格按以下 JSON 格式返回，不要有任何其他内容：
```json
[
  {{
    "id": "1",
    "type": "choice",
    "text": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "A",
    "explanation": "解析内容",
    "knowledge_points": ["知识点1", "知识点2"],
    "difficulty": 2
  }}
]
```

只返回 JSON 数组，不要有任何其他文字说明。"""

            logger.info(f"[强化题生成] 开始生成, weak_points={request.weak_points}")

            # 获取当前小节已有的最大 order_index
            max_order_result = await db.execute(
                select(func.max(SectionBaseQuestion.order_index)).where(
                    SectionBaseQuestion.section_id == request.section_id,
                    SectionBaseQuestion.is_active,
                )
            )
            max_order = max_order_result.scalar() or 0
            logger.info(f"[强化题生成] 当前最大 order_index: {max_order}")

            response = await ai_service.generate(prompt)
            logger.info(f"[强化题生成] AI响应: {response[:500]}...")

            # 解析 AI 响应
            questions = []
            db_questions = []
            try:
                # 尝试提取 JSON 数组
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    json_str = json_match.group(0)
                    raw_questions = json.loads(json_str)

                    for i, q in enumerate(raw_questions[:request.question_count]):
                        question = EnhancedQuizQuestion(
                            id=q.get('id', str(i + 1)),
                            type=q.get('type', 'choice'),
                            text=q.get('text', ''),
                            options=q.get('options', []),
                            correct_answer=q.get('correct_answer', ''),
                            explanation=q.get('explanation', ''),
                            knowledge_points=q.get('knowledge_points', []),
                            difficulty=q.get('difficulty', 2),
                        )
                        questions.append(question)

                        # 创建数据库记录
                        # order_index 从当前最大值+1开始，追加到后面
                        db_question = SectionBaseQuestion(
                            section_id=request.section_id,
                            chapter_id=request.chapter_id,
                            user_id=user_id,
                            question_source='enhanced',
                            order_index=max_order + i + 1,
                            question_type=q.get('type', 'choice'),
                            question_text=q.get('text', ''),
                            options=q.get('options', []),
                            correct_answer=q.get('correct_answer', ''),
                            explanation=q.get('explanation', ''),
                            knowledge_points=q.get('knowledge_points', []),
                            difficulty=q.get('difficulty', 2),
                            is_active=True,
                        )
                        db_questions.append(db_question)

                    logger.info(f"[强化题生成] 成功解析 {len(questions)} 道题目")
                else:
                    logger.warning(f"[强化题生成] 未找到 JSON 数组，响应: {response[:200]}")
            except json.JSONDecodeError as e:
                logger.error(f"[强化题生成] JSON 解析失败: {e}")
                # 如果解析失败，创建一些默认题目
                for i, kp in enumerate(request.weak_points[:request.question_count]):
                    questions.append(EnhancedQuizQuestion(
                        id=str(i + 1),
                        type="choice",
                        text=f"关于 {kp} 的练习题（AI生成失败，请稍后重试）",
                        options=["选项A", "选项B", "选项C", "选项D"],
                        correct_answer="A",
                        explanation=f"本题考查 {kp} 相关知识",
                        knowledge_points=[kp],
                        difficulty=2,
                    ))

            # 持久化到数据库
            if db_questions:
                db.add_all(db_questions)
                await db.commit()
                # 刷新获取 ID
                for q in db_questions:
                    await db.refresh(q)
                logger.info(f"[强化题生成] 已保存 {len(db_questions)} 道题目到数据库")

            session_id = str(uuid.uuid4())

            # 更新返回的题目 ID 为数据库 ID
            for i, (q, db_q) in enumerate(zip(questions, db_questions)):
                q.id = str(db_q.id)

            # 存储会话（内存中保留一份副本）
            self._enhanced_sessions[session_id] = EnhancedQuizSession(
                session_id=session_id,
                user_id=user_id,
                section_id=request.section_id,
                chapter_id=request.chapter_id,
                course_id=request.course_id,
                questions=[q.model_dump() for q in questions],
            )

            return EnhancedQuizGenerateResponse(
                success=True,
                session_id=session_id,
                questions=questions,
                weak_points_addressed=request.weak_points,
                message=f"成功生成 {len(questions)} 道强化题"
            )

        except Exception as e:
            logger.error(f"[强化题生成] 异常: {e}")
            return EnhancedQuizGenerateResponse(
                success=False,
                message=f"生成强化题失败: {str(e)}"
            )

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

        session = self._enhanced_sessions.get(request.session_id)
        if not session:
            return EnhancedQuizSubmitResponse(
                success=False,
                session_id=request.session_id,
                section_id=request.section_id,
                total_questions=0,
                correct_answers=0,
                accuracy=0,
                message="会话不存在或已过期"
            )

        # 计算结果
        results = []
        correct_count = 0

        for answer in request.answers:
            question = next(
                (q for q in session.questions if q.get("id") == answer.get("question_id")),
                None
            )
            if question:
                is_correct = answer.get("answer", "").strip().upper() == question.get("correct_answer", "").strip().upper()
                if is_correct:
                    correct_count += 1
                results.append({
                    "question_id": answer.get("question_id"),
                    "is_correct": is_correct,
                    "user_answer": answer.get("answer"),
                    "correct_answer": question.get("correct_answer"),
                })

        accuracy = correct_count / len(session.questions) if session.questions else 0
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

        # 清理会话
        del self._enhanced_sessions[request.session_id]

        return EnhancedQuizSubmitResponse(
            success=True,
            session_id=request.session_id,
            section_id=request.section_id,
            total_questions=len(session.questions),
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
