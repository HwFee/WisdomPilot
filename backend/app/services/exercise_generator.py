"""Exercise Generator Service - 流式题目生成服务

实现逐题生成题目的流式生成模式：
1. 第一题生成后立即返回给前端
2. 剩余题目在后台异步生成
3. 通过回调函数通知前端新题目

基于 Andrej Karpathy 的原则：
- 简单直白的实现
- 单一职责
- 清晰的错误处理
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Awaitable
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.exercise_generation import ExerciseGenerationSession
from app.services.ai import ai_service


logger = logging.getLogger(__name__)

# 回调类型定义
ExerciseGeneratedCallback = Callable[[int, dict, int, int], Awaitable[None]]
"""回调函数: (index, exercise, current_count, total_count)"""


class ExerciseGeneratorService:
    """流式题目生成服务

    核心方法:
    - generate_first_then_stream: 生成第一题并返回，剩余题目异步生成
    - get_session: 获取会话状态
    - get_all_exercises: 获取会话已生成的所有题目
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_first_then_stream(
        self,
        user_id: str,
        session_type: str,
        section_id: Optional[int],
        chapter_id: Optional[int],
        course_id: Optional[int],
        weak_points: list[str],
        strong_points: list[str],
        question_count: int,
        section_title: str,
        chapter_title: str,
        progress_callback: Optional[ExerciseGeneratedCallback] = None,
    ) -> tuple[str, dict, int]:
        """生成第一题并返回，剩余题目异步生成

        Args:
            user_id: 用户ID
            session_type: "enhanced" | "challenge"
            section_id: 小节ID
            chapter_id: 章节ID
            course_id: 课程ID
            weak_points: 薄弱点列表
            strong_points: 已掌握知识点
            question_count: 总共要生成的题目数
            section_title: 小节标题
            chapter_title: 章节标题
            progress_callback: 每生成一题的回调函数

        Returns:
            (session_id, first_exercise, remaining_count)
        """
        # 创建生成会话
        session = ExerciseGenerationSession(
            user_id=user_id,
            session_type=session_type,
            section_id=section_id,
            chapter_id=chapter_id,
            course_id=course_id,
            request_data={
                "weak_points": weak_points,
                "strong_points": strong_points,
                "question_count": question_count,
                "section_title": section_title,
                "chapter_title": chapter_title,
            },
            total_count=question_count,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # 生成第一题（阻塞）
        first_exercise = await self._generate_single_exercise(
            index=0,
            weak_points=weak_points,
            strong_points=strong_points,
            section_title=section_title,
            chapter_title=chapter_title,
        )

        if first_exercise is None:
            session.fail("第一题生成失败")
            await self.db.commit()
            raise ValueError("生成题目失败，请稍后重试")

        # 保存第一题
        session.add_exercise(first_exercise)
        await self.db.commit()

        # 启动后台任务生成剩余题目
        remaining_count = question_count - 1
        if remaining_count > 0:
            # 创建独立的数据库会话来避免阻塞主请求
            asyncio.create_task(
                self._generate_remaining_async(
                    session_id=session.id,
                    user_id=user_id,
                    section_title=section_title,
                    chapter_title=chapter_title,
                    weak_points=weak_points,
                    strong_points=strong_points,
                    start_index=1,
                    total_count=question_count,
                    progress_callback=progress_callback,
                )
            )

        return session.id, first_exercise, remaining_count

    async def _generate_remaining_async(
        self,
        session_id: str,
        user_id: str,
        section_title: str,
        chapter_title: str,
        weak_points: list[str],
        strong_points: list[str],
        start_index: int,
        total_count: int,
        progress_callback: Optional[ExerciseGeneratedCallback],
    ) -> None:
        """后台异步生成剩余题目

        使用独立的数据库会话来避免与主请求冲突。
        """
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            service = ExerciseGeneratorService(db)

            try:
                for i in range(start_index, total_count):
                    exercise = await service._generate_single_exercise(
                        index=i,
                        weak_points=weak_points,
                        strong_points=strong_points,
                        section_title=section_title,
                        chapter_title=chapter_title,
                    )

                    if exercise is None:
                        logger.error(f"第{i+1}题生成失败")
                        # 继续生成下一题，不中断
                        continue

                    # 保存到数据库
                    await service._append_exercise(session_id, exercise)

                    # 调用进度回调
                    if progress_callback:
                        try:
                            await progress_callback(i, exercise, i + 1, total_count)
                        except Exception as e:
                            logger.error(f"进度回调失败: {e}")

                # 标记完成
                await service._complete_session(session_id)
                logger.info(f"会话 {session_id[:8]}... 题目生成完成")

            except Exception as e:
                logger.error(f"后台生成任务失败: {e}")
                await service._fail_session(session_id, str(e))

    async def _generate_single_exercise(
        self,
        index: int,
        weak_points: list[str],
        strong_points: list[str],
        section_title: str,
        chapter_title: str,
    ) -> Optional[dict]:
        """生成单道题目

        使用简单直接的AI提示词，解析JSON响应。
        失败返回None，让调用者决定如何处理。
        """
        # 为每道题选择不同的薄弱点作为重点
        focus_weak_point = weak_points[index % len(weak_points)] if weak_points else "基础知识"

        prompt = f"""你是一个专业的编程教育题目出题专家。请根据以下信息生成1道强化练习题。

课程: C语言程序设计
章节: {chapter_title}
小节: {section_title}
本题重点考查: {focus_weak_point}
已掌握知识点: {', '.join(strong_points) if strong_points else '无'}

要求：
1. 题目要针对薄弱知识点进行强化训练
2. 难度适中（难度等级2-3）
3. 提供清晰的解析

请严格按以下 JSON 格式返回，不要有任何其他内容：
```json
{{
  "id": "temp_{index}",
  "type": "choice",
  "text": "题目内容",
  "options": ["选项A", "选项B", "选项C", "选项D"],
  "correct_answer": "A",
  "explanation": "解析内容",
  "knowledge_points": ["知识点1"],
  "difficulty": 2
}}
```

只返回 JSON 对象，不要有任何其他文字说明。"""

        try:
            response = await ai_service.generate(prompt)

            # 解析 JSON
            exercise = self._parse_exercise_response(response, index)

            if exercise:
                logger.info(f"第{index+1}题生成成功")
                return exercise
            else:
                logger.error(f"第{index+1}题解析失败")
                return None

        except Exception as e:
            logger.error(f"第{index+1}题生成异常: {e}")
            return None

    def _parse_exercise_response(self, response: str, index: int) -> Optional[dict]:
        """解析AI返回的题目JSON

        尝试多种方式提取JSON:
        1. 查找```json代码块
        2. 查找{}包围的对象
        """
        import re

        try:
            # 尝试提取 ```json 代码块
            json_match = re.search(r'```json\s*({[\s\S]*?})\s*```', response)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # 尝试查找任何JSON对象
            json_match = re.search(r'({[\s\S]*?"text"[\s\S]*?"knowledge_points"[\s\S]*?})', response)
            if json_match:
                return json.loads(json_match.group(1))

            # 直接尝试解析整个响应
            response_clean = response.strip()
            if response_clean.startswith('{') and response_clean.endswith('}'):
                return json.loads(response_clean)

            logger.warning(f"无法解析响应: {response[:200]}")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应: {response[:200]}")
            return None

    async def _append_exercise(self, session_id: str, exercise: dict) -> None:
        """追加题目到会话"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.add_exercise(exercise)
            await self.db.commit()

    async def _complete_session(self, session_id: str) -> None:
        """标记会话完成"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.complete()
            await self.db.commit()

    async def _fail_session(self, session_id: str, error: str) -> None:
        """标记会话失败"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.fail(error)
            await self.db.commit()

    async def get_session(self, session_id: str) -> Optional[ExerciseGenerationSession]:
        """获取会话"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all_exercises(self, session_id: str) -> list[dict]:
        """获取会话已生成的所有题目"""
        session = await self.get_session(session_id)
        if session:
            return session.generated_exercises
        return []


# 单例工厂函数
def get_exercise_generator_service(db: AsyncSession) -> ExerciseGeneratorService:
    return ExerciseGeneratorService(db)
