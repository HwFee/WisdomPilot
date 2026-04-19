"""
Mastery Quiz Service - 精进之路测试服务

提供知识点获取、AI 生成测试题、提交测试等功能。
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.chapter_mastery import ChapterMastery
from app.services.ai import ai_service
from app.schemas.mastery_quiz import (
    MasteryQuizGenerateRequest,
    MasteryQuizGenerateResponse,
    MasteryQuizSubmitRequest,
    MasteryQuizSubmitResponse,
    MasteryQuizQuestion,
    QuestionResult,
    UserProfileForQuiz,
    KnowledgePoint,
)
from app.utils.time import utc_now


class MasteryQuizSession(BaseModel):
    """测试会话模型（内存中临时存储）"""
    id: str
    user_id: str
    course_id: int
    chapter_id: int
    questions: list[dict]
    created_at: datetime
    expires_at: datetime


class MasteryQuizService:
    """精进之路测试服务

    注意：当前使用内存存储会话，适用于单实例部署。
    生产环境多实例部署时，应配置 Redis 存储：

    配置方式：
    1. 设置环境变量: REDIS_URL=redis://localhost:6379/0
    2. 安装依赖: pip install redis
    3. 将 _sessions 替换为 Redis 存储

    TODO: 添加 Redis 存储支持
    """

    # 内存中的会话存储（单实例适用）
    # 生产环境多实例应使用 Redis: {session_id: MasteryQuizSession}
    _sessions: dict[str, MasteryQuizSession] = {}

    async def get_chapter_knowledge_content(
        self,
        db: AsyncSession,
        chapter_id: int,
        user_id: str,
    ) -> Optional[dict]:
        """
        获取章节知识点内容

        Args:
            db: 数据库会话
            chapter_id: 章节ID
            user_id: 用户ID

        Returns:
            知识点内容字典，包含章节信息和知识点列表
        """
        chapter, course = await self._get_chapter_with_course(db, chapter_id)
        if not chapter:
            return None

        # 生成或获取知识点
        knowledge_data = await self._generate_or_get_knowledge(
            db=db,
            chapter=chapter,
            course=course,
            user_id=user_id
        )

        if not knowledge_data:
            return None

        return {
            "chapter_id": chapter.id,
            "chapter_title": chapter.title,
            "knowledge_points": knowledge_data.get("knowledge_points", []),
            "total_points": len(knowledge_data.get("knowledge_points", [])),
            "estimated_time": knowledge_data.get("estimated_time", 15),
            "prerequisites": None,
            "next_chapters": None,
        }

    async def generate_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: MasteryQuizGenerateRequest,
    ) -> dict:
        """
        生成个性化测试题

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 生成请求

        Returns:
            生成结果，包含题目列表
        """
        # 获取章节信息
        chapter = await self._get_chapter(db, request.chapter_id)
        if not chapter:
            return {
                "success": False,
                "session_id": "",
                "questions": [],
                "user_profile_used": False,
                "weak_points_addressed": [],
                "message": "未找到章节"
            }

        # 获取用户画像
        user_profile = await self._get_user_profile(
            db=db,
            user_id=user_id,
            course_id=request.course_id
        )

        # 生成测试题
        questions = await self._generate_quiz_questions(
            chapter=chapter,
            user_profile=user_profile,
            request=request
        )

        if not questions:
            return {
                "success": False,
                "session_id": "",
                "questions": [],
                "user_profile_used": user_profile is not None,
                "weak_points_addressed": [],
                "message": "AI 服务暂时不可用，请稍后重试"
            }

        # 创建会话
        session_id = await self._create_quiz_session(
            user_id=user_id,
            course_id=request.course_id,
            chapter_id=request.chapter_id,
            questions=questions
        )

        # 提取针对的薄弱点
        weak_points_addressed = []
        if user_profile and user_profile.get("weak_knowledge_points"):
            weak_points = set(user_profile["weak_knowledge_points"])
            for q in questions:
                for kp in q.get("knowledge_points", []):
                    if kp in weak_points:
                        weak_points_addressed.append(kp)
            weak_points_addressed = list(set(weak_points_addressed))

        return {
            "success": True,
            "session_id": session_id,
            "questions": questions,
            "user_profile_used": user_profile is not None,
            "weak_points_addressed": weak_points_addressed,
            "message": f"成功生成 {len(questions)} 道测试题"
        }

    async def submit_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        request: MasteryQuizSubmitRequest,
    ) -> dict:
        """
        提交测试结果

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 提交请求

        Returns:
            测试结果
        """
        # 获取会话
        session = await self._get_quiz_session(request.session_id)
        if not session:
            return {
                "success": False,
                "session_id": request.session_id,
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0,
                "xp_earned": 0,
                "mastery_points_earned": 0,
                "results": [],
                "recommendations": [],
                "passed": False,
                "message": "会话不存在或已过期"
            }

        # 验证用户
        if session.user_id != user_id:
            return {
                "success": False,
                "session_id": request.session_id,
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0,
                "xp_earned": 0,
                "mastery_points_earned": 0,
                "results": [],
                "recommendations": [],
                "passed": False,
                "message": "无权访问此会话"
            }

        # 评估答案
        evaluation = await self._evaluate_answers(
            session=session,
            answers=request.answers
        )

        # 计算经验值和掌握点
        accuracy = evaluation["correct_count"] / evaluation["total_count"] if evaluation["total_count"] > 0 else 0
        xp_earned = int(accuracy * 50)  # 最高 50 XP
        mastery_points_earned = int(accuracy * 20)  # 最高 20 掌握点

        # 更新用户进度
        await self._update_user_progress(
            db=db,
            user_id=user_id,
            chapter_id=session.chapter_id,
            correct_count=evaluation["correct_count"],
            total_count=evaluation["total_count"]
        )

        # 生成学习建议
        recommendations = self._generate_recommendations(
            results=evaluation["results"],
            accuracy=accuracy
        )

        # 清理会话
        self._sessions.pop(request.session_id, None)

        return {
            "success": True,
            "session_id": request.session_id,
            "total_questions": evaluation["total_count"],
            "correct_answers": evaluation["correct_count"],
            "accuracy": accuracy,
            "xp_earned": xp_earned,
            "mastery_points_earned": mastery_points_earned,
            "results": evaluation["results"],
            "recommendations": recommendations,
            "passed": accuracy >= 0.8,
            "message": "提交成功" + ("，恭喜通过！" if accuracy >= 0.8 else "")
        }

    # ========================================
    # Private Helper Methods
    # ========================================

    async def _get_chapter_with_course(
        self,
        db: AsyncSession,
        chapter_id: int
    ) -> tuple[Optional[Chapter], Optional[Course]]:
        """获取章节和关联的课程"""
        result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            return None, None

        course_result = await db.execute(
            select(Course).where(Course.id == chapter.course_id)
        )
        course = course_result.scalar_one_or_none()

        return chapter, course

    async def _get_chapter(self, db: AsyncSession, chapter_id: int) -> Optional[Chapter]:
        """获取章节"""
        result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        return result.scalar_one_or_none()

    async def _generate_or_get_knowledge(
        self,
        db: AsyncSession,
        chapter: Chapter,
        course: Optional[Course],
        user_id: str,
    ) -> Optional[dict]:
        """生成或获取知识点"""
        if not ai_service.is_configured():
            # 返回默认知识点
            return {
                "knowledge_points": [
                    {
                        "id": f"kp_{chapter.id}_default",
                        "title": chapter.title,
                        "content": chapter.description or "本章节的知识点内容正在生成中...",
                        "examples": [],
                        "difficulty": 1,
                        "related_points": []
                    }
                ],
                "cached": False
            }

        # 使用 AI 生成知识点
        knowledge_data = await ai_service.generate_knowledge_content(
            chapter_title=chapter.title,
            chapter_description=chapter.description or "",
            course_name=course.name if course else "编程"
        )

        if not knowledge_data:
            return {
                "knowledge_points": [
                    {
                        "id": f"kp_{chapter.id}_default",
                        "title": chapter.title,
                        "content": chapter.description or "知识点内容",
                        "examples": [],
                        "difficulty": 1,
                        "related_points": []
                    }
                ],
                "cached": False
            }

        knowledge_data["cached"] = False
        return knowledge_data

    async def _get_user_profile(
        self,
        db: AsyncSession,
        user_id: str,
        course_id: int
    ) -> Optional[dict]:
        """获取用户画像"""
        # 获取用户在各章节的掌握情况
        result = await db.execute(
            select(ChapterMastery).where(
                and_(
                    ChapterMastery.user_id == user_id,
                    ChapterMastery.course_id == course_id
                )
            )
        )
        masteries = result.scalars().all()

        if not masteries:
            return None

        # 计算当前水平
        total_mastery = sum(m.mastery_score for m in masteries)
        avg_mastery = total_mastery / len(masteries) if masteries else 0
        current_level = min(5.0, max(1.0, avg_mastery / 20))  # 转换为 1-5

        # 识别薄弱知识点
        weak_knowledge_points = []
        strong_knowledge_points = []

        for m in masteries:
            if m.mastery_score < 50:
                weak_knowledge_points.extend(m.objectives_status or [])
            elif m.mastery_score >= 80:
                strong_knowledge_points.extend(m.objectives_status or [])

        # 计算近期正确率
        total_exercises = sum(m.total_exercises for m in masteries)
        correct_exercises = sum(m.correct_exercises for m in masteries)
        recent_accuracy = correct_exercises / total_exercises if total_exercises > 0 else 0.5

        return {
            "user_id": user_id,
            "current_level": current_level,
            "weak_knowledge_points": list(set(weak_knowledge_points)),
            "strong_knowledge_points": list(set(strong_knowledge_points)),
            "recent_accuracy": recent_accuracy,
        }

    async def _generate_quiz_questions(
        self,
        chapter: Chapter,
        user_profile: Optional[dict],
        request: MasteryQuizGenerateRequest
    ) -> list[dict]:
        """生成测试题"""
        if not ai_service.is_configured():
            # 返回示例题目
            return [{
                "id": f"q_sample_{i}",
                "type": "choice",
                "difficulty": 2,
                "content": {
                    "text": f"示例题目 {i+1}：关于 {chapter.title} 的知识点",
                    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"]
                },
                "solution": {"answer": "A", "explanation": "示例解析"},
                "knowledge_points": [chapter.title]
            } for i in range(min(request.question_count, 3))]

        # 使用 AI 生成题目
        questions = await ai_service.generate_personalized_quiz(
            chapter_title=chapter.title,
            chapter_description=chapter.description or "",
            user_profile=user_profile,
            question_count=request.question_count,
            question_types=request.question_types,
            difficulty_range=request.difficulty_range
        )

        return questions

    async def _create_quiz_session(
        self,
        user_id: str,
        course_id: int,
        chapter_id: int,
        questions: list[dict]
    ) -> str:
        """创建测试会话"""
        session_id = str(uuid.uuid4())
        now = utc_now()

        session = MasteryQuizSession(
            id=session_id,
            user_id=user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            questions=questions,
            created_at=now,
            expires_at=datetime.fromtimestamp(now.timestamp() + 3600)  # 1小时后过期
        )

        self._sessions[session_id] = session
        return session_id

    async def _get_quiz_session(self, session_id: str) -> Optional[MasteryQuizSession]:
        """获取测试会话"""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # 检查是否过期
        if session.expires_at < utc_now():
            self._sessions.pop(session_id, None)
            return None

        return session

    async def _evaluate_answers(
        self,
        session: MasteryQuizSession,
        answers: list[Any]
    ) -> dict:
        """评估答案"""
        questions_map = {q["id"]: q for q in session.questions}

        results = []
        correct_count = 0

        for answer in answers:
            question_id = answer.question_id
            user_answer = answer.answer

            question = questions_map.get(question_id)
            if not question:
                continue

            correct_answer = question.get("solution", {}).get("answer", "")
            is_correct = str(user_answer) == str(correct_answer)

            if is_correct:
                correct_count += 1

            results.append({
                "question_id": question_id,
                "is_correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "explanation": question.get("solution", {}).get("explanation", ""),
                "knowledge_points": question.get("knowledge_points", [])
            })

        return {
            "correct_count": correct_count,
            "total_count": len(session.questions),
            "results": results
        }

    async def _update_user_progress(
        self,
        db: AsyncSession,
        user_id: str,
        chapter_id: int,
        correct_count: int,
        total_count: int
    ) -> None:
        """更新用户进度

        更新 ChapterMastery 记录：
        - 增加练习次数
        - 更新正确率
        - 更新掌握分数
        """
        # 获取或创建 ChapterMastery 记录
        result = await db.execute(
            select(ChapterMastery).where(
                and_(
                    ChapterMastery.user_id == user_id,
                    ChapterMastery.chapter_id == chapter_id
                )
            )
        )
        mastery = result.scalar_one_or_none()

        if mastery:
            # 更新现有记录
            mastery.total_exercises += total_count
            mastery.correct_exercises += correct_count

            # 重新计算分数
            accuracy = mastery.correct_exercises / mastery.total_exercises if mastery.total_exercises > 0 else 0
            mastery.accuracy_score = accuracy * 100
            mastery.mastery_score = min(100, mastery.mastery_score + (accuracy * 10))
            mastery.mastery_level = self._get_mastery_level(mastery.mastery_score)
        else:
            # 创建新记录
            accuracy = correct_count / total_count if total_count > 0 else 0
            mastery = ChapterMastery(
                user_id=user_id,
                course_id=0,  # Will be set by caller if needed
                chapter_id=chapter_id,
                total_exercises=total_count,
                correct_exercises=correct_count,
                accuracy_score=accuracy * 100,
                mastery_score=min(100, accuracy * 50),
                mastery_level=self._get_mastery_level(accuracy * 50),
            )
            db.add(mastery)

        await db.commit()

    def _get_mastery_level(self, score: float) -> str:
        """根据分数获取掌握等级"""
        if score >= 90:
            return "精通"
        elif score >= 75:
            return "熟练"
        elif score >= 60:
            return "练习"
        elif score >= 40:
            return "学习"
        else:
            return "入门"

    def _generate_recommendations(
        self,
        results: list[dict],
        accuracy: float
    ) -> list[str]:
        """生成学习建议"""
        recommendations = []

        if accuracy >= 0.9:
            recommendations.append("表现优秀！可以尝试更高难度的内容。")
        elif accuracy >= 0.7:
            recommendations.append("掌握良好，建议复习错误的知识点。")
        else:
            recommendations.append("建议重新学习相关知识点后再进行测试。")

        # 添加具体知识点建议
        wrong_topics = []
        for r in results:
            if not r["is_correct"]:
                wrong_topics.extend(r.get("knowledge_points", []))

        if wrong_topics:
            unique_topics = list(set(wrong_topics))[:3]
            recommendations.append(f"重点复习：{', '.join(unique_topics)}")

        return recommendations


# 全局单例
mastery_quiz_service = MasteryQuizService()
