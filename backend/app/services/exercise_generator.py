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

# 限制并发 API 调用数（避免触发服务商速率限制）
_api_semaphore = asyncio.Semaphore(3)
# 保护数据库写入（避免并发修改 JSON 列导致数据丢失）
# 全局锁，防止多任务同时写入同一 session 的 JSON 列
_db_write_lock = asyncio.Lock()


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
        """点击即同时生成所有题目，返回第一题

        核心改动：不再阻塞生成第一题。创建session后立即在后台
        并发启动全部题目的生成，主请求只轮询等待第一题落库。

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

        # 立即在后台并发启动全部题目的生成（包括第1题）
        asyncio.create_task(
            self._generate_all_async(
                session_id=session.id,
                user_id=user_id,
                section_title=section_title,
                chapter_title=chapter_title,
                weak_points=weak_points,
                strong_points=strong_points,
                total_count=question_count,
                progress_callback=progress_callback,
            )
        )

        # 轮询等待第一题落库（最多等60秒）
        # 注意：使用独立 session 查询，避免事务隔离导致看不到后台写入
        first_exercise = None
        from app.database import AsyncSessionLocal
        for _ in range(120):  # 120 * 0.5s = 60s
            await asyncio.sleep(0.5)
            async with AsyncSessionLocal() as poll_db:
                poll_service = ExerciseGeneratorService(poll_db)
                db_session = await poll_service.get_session(session.id)
                if db_session and db_session.generated_exercises:
                    # 按 index 查找第一题（index=0）
                    first = next(
                        (ex for ex in db_session.generated_exercises if ex.get("index") == 0),
                        None
                    )
                    if first:
                        first_exercise = first
                        break
                    # 兜底：如果还没有 index=0，但至少有一题，先返回（旧数据兼容）
                    first_exercise = db_session.generated_exercises[0]
                    break

        if first_exercise is None:
            raise ValueError("生成题目失败，请稍后重试")

        return session.id, first_exercise, question_count - 1

    async def _generate_all_async(
        self,
        session_id: str,
        user_id: str,
        section_title: str,
        chapter_title: str,
        weak_points: list[str],
        strong_points: list[str],
        total_count: int,
        progress_callback: Optional[ExerciseGeneratedCallback],
    ) -> None:
        """后台异步生成全部题目（并发生成，串行写入）

        所有题目从点击那一刻同时开始生成（受信号量限制并发数），
        生成完成后串行写入数据库（受锁保护避免竞争）。
        """
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            service = ExerciseGeneratorService(db)

            async def generate_one(index: int) -> None:
                task_start = datetime.now(timezone.utc)
                logger.info(f"[T{index+1}] 任务启动")

                # 1. 生成题目（并发，但受信号量限制避免 API 速率限制）
                async with _api_semaphore:
                    sem_acquired = datetime.now(timezone.utc)
                    logger.info(f"[T{index+1}] 获取信号量, 等待={(sem_acquired - task_start).total_seconds():.3f}s")
                    exercise = await service._generate_single_exercise(
                        index=index,
                        weak_points=weak_points,
                        strong_points=strong_points,
                        section_title=section_title,
                        chapter_title=chapter_title,
                    )
                    api_done = datetime.now(timezone.utc)
                    logger.info(f"[T{index+1}] API调用完成, 耗时={(api_done - sem_acquired).total_seconds():.3f}s")

                if exercise is None:
                    logger.error(f"第{index + 1}题生成失败")
                    return

                # 2. 写入数据库（串行，避免并发修改 JSON 列）
                lock_wait_start = datetime.now(timezone.utc)
                try:
                    async with asyncio.timeout(15.0):
                        async with _db_write_lock:
                            lock_acquired = datetime.now(timezone.utc)
                            logger.info(f"[T{index+1}] 获取DB锁, 等待={(lock_acquired - lock_wait_start).total_seconds():.3f}s")
                            await service._append_exercise(session_id, exercise)
                            await db.commit()
                            db_done = datetime.now(timezone.utc)
                            logger.info(f"[T{index+1}] DB写入完成, 耗时={(db_done - lock_acquired).total_seconds():.3f}s")
                except asyncio.TimeoutError:
                    logger.error(f"[T{index+1}] 获取DB锁超时(15s)，放弃写入")
                    return

                # 3. 回调通知
                if progress_callback:
                    try:
                        await progress_callback(index, exercise, index + 1, total_count)
                    except Exception as e:
                        logger.error(f"进度回调失败: {e}")

                task_done = datetime.now(timezone.utc)
                logger.info(f"[T{index+1}] 任务总耗时={(task_done - task_start).total_seconds():.3f}s")

            try:
                # 并发启动所有题目的生成（从0开始，包括第一题）
                tasks = [
                    generate_one(i)
                    for i in range(total_count)
                ]
                gather_start = datetime.now(timezone.utc)
                logger.info(f"[{session_id[:8]}] asyncio.gather() 开始, 共{total_count}个任务")
                results = await asyncio.gather(*tasks, return_exceptions=True)
                gather_end = datetime.now(timezone.utc)
                logger.info(f"[{session_id[:8]}] asyncio.gather() 完成, 总耗时={(gather_end - gather_start).total_seconds():.3f}s")

                # 统计失败任务
                failed_count = sum(1 for r in results if isinstance(r, Exception))
                if failed_count > 0:
                    logger.warning(f"[{session_id[:8]}] {failed_count}/{total_count} 道题生成失败")

                # 检查是否至少生成了一道题
                db_session = await service.get_session(session_id)
                if db_session and db_session.generated_count > 0:
                    async with _db_write_lock:
                        await service._complete_session(session_id)
                        await db.commit()
                    logger.info(f"会话 {session_id[:8]}... 题目生成完成 ({db_session.generated_count}/{total_count})")
                else:
                    async with _db_write_lock:
                        await service._fail_session(session_id, "所有题目生成失败")
                        await db.commit()
                    logger.error(f"会话 {session_id[:8]}... 所有题目生成失败")

            except Exception as e:
                logger.error(f"后台生成任务失败: {e}")
                async with _db_write_lock:
                    await service._fail_session(session_id, str(e))
                    await db.commit()

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
            api_start = datetime.now(timezone.utc)
            response = await ai_service.generate(prompt)
            api_end = datetime.now(timezone.utc)
            logger.info(f"[T{index+1}] ai_service.generate() 耗时={(api_end - api_start).total_seconds():.3f}s")

            # 解析 JSON
            parse_start = datetime.now(timezone.utc)
            exercise = self._parse_exercise_response(response, index)
            parse_end = datetime.now(timezone.utc)
            logger.info(f"[T{index+1}] JSON解析耗时={(parse_end - parse_start).total_seconds():.3f}s")

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
        """追加题目到会话（注意：调用方负责 commit）"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.add_exercise(exercise)
        else:
            logger.error(f"_append_exercise: session {session_id[:8]}... not found")

    async def _complete_session(self, session_id: str) -> None:
        """标记会话完成（注意：调用方负责 commit）"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.complete()
        else:
            logger.error(f"_complete_session: session {session_id[:8]}... not found")

    async def _fail_session(self, session_id: str, error: str) -> None:
        """标记会话失败（注意：调用方负责 commit）"""
        result = await self.db.execute(
            select(ExerciseGenerationSession).where(
                ExerciseGenerationSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.fail(error)
        else:
            logger.error(f"_fail_session: session {session_id[:8]}... not found")

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
