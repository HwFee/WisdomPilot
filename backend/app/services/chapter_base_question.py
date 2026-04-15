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
    ) -> BaseAnswersSubmitResponse:
        """
        提交基础题答案并分析薄弱点

        Args:
            db: 数据库会话
            chapter_id: 章节ID
            request: 答案提交请求

        Returns:
            包含结果分析和薄弱点识别的响应
        """
        # 获取题目
        questions_result = await db.execute(
            select(ChapterBaseQuestion)
            .where(ChapterBaseQuestion.chapter_id == chapter_id, ChapterBaseQuestion.is_active == True)
            .order_by(ChapterBaseQuestion.order_index)
        )
        questions = {q.id: q for q in questions_result.scalars().all()}

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

        # 识别薄弱点和强项
        weak_points = []
        strong_points = []

        for kp, stats in knowledge_stats.items():
            kp_accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if kp_accuracy < 0.5:
                weak_points.append(kp)
            elif kp_accuracy >= 0.8:
                strong_points.append(kp)

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
        生成个性化强化测试题

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 生成请求

        Returns:
            包含强化测试题的响应
        """
        # 获取章节信息
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == request.chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        if not chapter:
            return EnhancedQuizGenerateResponse(
                success=False,
                message="章节不存在",
            )

        # 使用 AI 生成强化题
        questions = await self._generate_enhanced_questions_with_ai(
            chapter=chapter,
            weak_points=request.weak_points,
            question_count=request.question_count,
            question_types=request.question_types,
        )

        if not questions:
            return EnhancedQuizGenerateResponse(
                success=False,
                message="AI 服务暂时不可用，请稍后重试",
            )

        # 创建会话
        session_id = str(uuid.uuid4())
        self._enhanced_sessions[session_id] = EnhancedQuizSession(
            session_id=session_id,
            user_id=user_id,
            chapter_id=request.chapter_id,
            course_id=request.course_id,
            questions=[q.model_dump() for q in questions],
        )

        return EnhancedQuizGenerateResponse(
            success=True,
            session_id=session_id,
            questions=questions,
            weak_points_addressed=request.weak_points,
            message=f"成功生成 {len(questions)} 道强化测试题",
        )

    async def submit_enhanced_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: EnhancedQuizSubmitRequest,
    ) -> EnhancedQuizSubmitResponse:
        """
        提交强化测试题答案

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 提交请求

        Returns:
            测试结果
        """
        # 获取会话
        session = self._enhanced_sessions.get(request.session_id)
        if not session or session.user_id != user_id:
            return EnhancedQuizSubmitResponse(
                success=False,
                session_id=request.session_id,
                total_questions=0,
                correct_answers=0,
                accuracy=0,
                message="会话不存在或已过期",
            )

        # 评估答案
        questions_map = {q["id"]: q for q in session.questions}
        results = []
        correct_count = 0

        for answer in request.answers:
            question_id = answer.get("question_id")
            user_answer = answer.get("answer", "")
            question = questions_map.get(question_id)

            if not question:
                continue

            # 获取正确答案
            correct_answer = question.get("correct_answer", "")
            is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()

            if is_correct:
                correct_count += 1

            results.append({
                "question_id": question_id,
                "is_correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "explanation": question.get("explanation", ""),
                "knowledge_points": question.get("knowledge_points", []),
            })

        total_questions = len(session.questions)
        accuracy = correct_count / total_questions if total_questions > 0 else 0
        xp_earned = int(accuracy * 30)
        mastery_points_earned = int(accuracy * 15)

        # 更新用户进度
        await self._update_user_progress(
            db=db,
            user_id=user_id,
            chapter_id=session.chapter_id,
            correct_count=correct_count,
            total_count=total_questions,
            course_id=session.course_id,
        )

        # 清理会话
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
        """使用 AI 生成强化测试题"""
        if not ai_service.is_configured():
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
            response = await ai_service.provider.generate_explanation(prompt)

            # 解析 JSON
            import json
            import re

            # 提取 JSON 数组
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response

            questions_data = json.loads(json_str)

            return [
                EnhancedQuizQuestion(
                    id=q.get("id", f"eq_{i}"),
                    type=q.get("type", "choice"),
                    difficulty=q.get("difficulty", 2),
                    text=q.get("text", ""),
                    options=q.get("options"),
                    code_template=q.get("code_template"),
                    test_cases=q.get("test_cases"),
                    knowledge_points=q.get("knowledge_points", []),
                )
                for i, q in enumerate(questions_data)
            ]
        except Exception as e:
            print(f"Failed to generate enhanced questions: {e}")
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
