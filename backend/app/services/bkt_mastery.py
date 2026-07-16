"""
BKT Mastery Service - BKT 掌握度服务

整合 BKT 模型与数据库操作，提供完整的掌握度管理功能。

核心功能：
1. 处理答题，更新 BKT 状态
2. 防刷分检测（适配 AI 生成题目场景）
3. 四层聚合：知识点 → 小节 → 章节 → 课程
4. 完成判定
"""

import logging
from typing import Optional, List, Dict, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_point_mastery import (
    KnowledgePointMastery,
    DEFAULT_P_L0,
    MASTERY_THRESHOLD,
)
from app.models.answer_history import AnswerHistory
from app.models.section_mastery import SectionMastery
from app.models.chapter_mastery import ChapterMastery
from app.models.course_mastery import CourseMastery
from app.services.bkt import BKTModel
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


class BKTMasteryService:
    """
    BKT 掌握度服务

    核心功能：
    1. 处理答题，更新 BKT 状态
    2. 防刷分检测（适配 AI 生成题目场景）
    3. 三层聚合：知识点 → 小节 → 章节 → 课程
    4. 完成判定
    """

    # 防刷分阈值（适配 AI 生成题目场景）
    MAX_KP_ATTEMPTS_PER_SECTION = (
        15  # 每小节每知识点最多计入次数（提高上限，避免正常答题被限制）
    )
    MAX_KP_ATTEMPTS_PER_HOUR = 50  # 每小时每知识点最多计入次数
    MIN_ANSWER_TIME_SECONDS = 3  # 最短答题时间（秒）- 降低以适应快速答题
    MAX_P_L_INCREASE_PER_SESSION = 0.35  # 单次会话掌握度增长上限

    def __init__(self, db: AsyncSession):
        self.db = db
        self.bkt_model = BKTModel()

    async def process_answer(
        self,
        user_id: str,
        question_source: str,
        question_id: int,
        is_correct: bool,
        knowledge_points: List[str],
        course_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        section_id: Optional[int] = None,
        difficulty: int = 1,
        question_type: str = "choice",
        user_answer: Optional[str] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> Dict:
        """
        处理答题，更新 BKT 状态

        这是核心方法，整合了：
        1. 防刷分检查
        2. BKT 更新
        3. 历史记录
        4. 章节聚合

        Args:
            user_id: 用户ID
            question_source: 题目来源 (mastery/challenge/exercise)
            question_id: 题目ID
            is_correct: 是否正确
            knowledge_points: 涉及的知识点列表
            course_id: 课程ID
            chapter_id: 章节ID
            section_id: 小节ID
            difficulty: 难度 1-3
            question_type: 题型 (choice/fill_blank)
            user_answer: 用户答案
            time_spent_seconds: 答题耗时

        Returns:
            {
                "counted": bool,           # 是否计入掌握度
                "not_counted_reason": str, # 不计入原因
                "mastery_changes": List,   # 各知识点变化
                "section_mastery": float,  # 小节聚合掌握度
                "chapter_mastery": float,  # 章节聚合掌握度
                "is_section_completed": bool, # 小节是否完成
                "is_chapter_completed": bool, # 章节是否完成
            }
        """
        logger.info("[BKT] ==================== BKT 答题处理开始 ====================")
        logger.info(f"[BKT] 用户: {user_id[:8]}...")
        logger.info(f"[BKT] 题目ID: {question_id} | 来源: {question_source}")
        logger.info(f"[BKT] 章节: {chapter_id} | 小节: {section_id}")
        logger.info(
            f"[BKT] 答题结果: {'[OK] 正确' if is_correct else '[X] 错误'} | 耗时: {time_spent_seconds}s"
        )
        logger.info(f"[BKT] 知识点: {knowledge_points}")
        logger.info("[BKT] ==========================================================")
        logger.info("[BKT] ==================== BKT 答题处理开始 ====================")
        logger.info(f"[BKT] 用户: {user_id[:8]}...")
        logger.info(f"[BKT] 题目ID: {question_id} | 来源: {question_source}")
        logger.info(f"[BKT] 章节: {chapter_id} | 小节: {section_id}")
        logger.info(
            f"[BKT] 答题结果: {'[OK] 正确' if is_correct else '[X] 错误'} | 耗时: {time_spent_seconds}s"
        )
        logger.info(f"[BKT] 知识点: {knowledge_points}")
        logger.info("[BKT] ==========================================================")

        # 如果没有知识点，直接返回
        if not knowledge_points:
            logger.warning(f"[BKT] 题目 {question_id} 没有关联知识点，无法更新掌握度")
            return {
                "counted": False,
                "not_counted_reason": "no_knowledge_points",
                "mastery_changes": [],
                "section_mastery": 0.0,
                "chapter_mastery": 0.0,
                "is_section_completed": False,
                "is_chapter_completed": False,
            }

        # Step 1: 防刷分检查
        counted, not_counted_reason = await self._check_should_count(
            user_id,
            question_source,
            question_id,
            knowledge_points,
            section_id=section_id,
            time_spent_seconds=time_spent_seconds,
        )

        logger.info("[BKT] ┌─────────────────────────────────────────────────")
        logger.info(f"[BKT] │ 防刷分检查: {'[OK] 通过' if counted else '[X] 未通过'}")
        if not counted:
            logger.info(f"[BKT] │ 不计入原因: {not_counted_reason}")
        logger.info("[BKT] └─────────────────────────────────────────────────")

        # Step 2: 获取 BKT 参数（根据题型和难度）
        base_params = self.bkt_model.get_question_type_params(question_type)
        temp_model = BKTModel(base_params)
        adjusted_params = temp_model.get_difficulty_adjusted_params(difficulty)
        temp_model = BKTModel(adjusted_params)

        logger.info("[BKT] ┌─────────────────────────────────────────────────")
        logger.info("[BKT] │ BKT 参数设置")
        logger.info(f"[BKT] │ 题型: {question_type} | 难度: {difficulty}")
        logger.info(
            f"[BKT] │ P(L0)={adjusted_params.p_l0:.2f}, P(T)={adjusted_params.p_t:.2f}"
        )
        logger.info(
            f"[BKT] │ P(G)={adjusted_params.p_g:.2f}, P(S)={adjusted_params.p_s:.2f}"
        )
        logger.info("[BKT] └─────────────────────────────────────────────────")

        # Step 3: 更新各知识点状态
        logger.info("[BKT] ┌─────────────────────────────────────────────────")
        logger.info(f"[BKT] │ 开始更新 {len(knowledge_points)} 个知识点的掌握状态")
        logger.info("[BKT] └─────────────────────────────────────────────────")

        mastery_changes = []
        p_l_sum_before = 0.0
        p_l_sum_after = 0.0

        for kp in knowledge_points:
            kp_mastery = await self._get_or_create_kp_mastery(
                user_id, kp, course_id, chapter_id, section_id
            )

            p_l_before = kp_mastery.p_l
            p_l_sum_before += p_l_before

            if counted:
                # 应用 BKT 更新
                p_l_after, is_mastered = temp_model.update(p_l_before, is_correct, kp)

                # 更新数据库
                kp_mastery.p_l = p_l_after
                kp_mastery.total_attempts += 1
                if is_correct:
                    kp_mastery.correct_attempts += 1
                kp_mastery.unique_questions += 1

                kp_mastery.last_attempt_at = utc_now()
                if not kp_mastery.first_attempt_at:
                    kp_mastery.first_attempt_at = utc_now()

                if is_mastered and not kp_mastery.mastered_at:
                    kp_mastery.mastered_at = utc_now()
                    logger.info(
                        f"[BKT] [*] 知识点 '{kp}' 达到掌握阈值！P(L) = {p_l_after:.4f}"
                    )
            else:
                p_l_after = p_l_before
                logger.info(f"[BKT] │ 知识点 '{kp}' 未计入掌握度（防刷分）")
                logger.info(f"[BKT] │ P(L) 保持不变 = {p_l_before:.4f}")

            p_l_sum_after += p_l_after
            mastery_changes.append(
                {
                    "knowledge_point": kp,
                    "p_l_before": p_l_before,
                    "p_l_after": p_l_after,
                    "is_mastered": kp_mastery.p_l >= MASTERY_THRESHOLD,
                }
            )

        # 计算平均掌握概率
        avg_p_l_before = (
            p_l_sum_before / len(knowledge_points) if knowledge_points else 0
        )
        avg_p_l_after = p_l_sum_after / len(knowledge_points) if knowledge_points else 0

        logger.info("[BKT] ┌─────────────────────────────────────────────────")
        logger.info("[BKT] │ 知识点更新汇总")
        logger.info(f"[BKT] │ 平均 P(L): {avg_p_l_before:.4f} → {avg_p_l_after:.4f}")
        logger.info(f"[BKT] │ 变化量: {avg_p_l_after - avg_p_l_before:+.4f}")
        logger.info("[BKT] └─────────────────────────────────────────────────")

        # Step 4: 记录答题历史
        await self._record_answer_history(
            user_id=user_id,
            question_source=question_source,
            question_id=question_id,
            is_correct=is_correct,
            knowledge_points=knowledge_points,
            counted=counted,
            not_counted_reason=not_counted_reason,
            course_id=course_id,
            chapter_id=chapter_id,
            user_answer=user_answer,
            time_spent_seconds=time_spent_seconds,
            p_l_before=avg_p_l_before,
            p_l_after=avg_p_l_after,
        )

        # Step 5: 更新小节聚合掌握度（如果有 section_id）
        section_mastery = 0.0
        is_section_completed = False

        if section_id:
            logger.info("[BKT] ┌─────────────────────────────────────────────────")
            logger.info(f"[BKT] │ 小节掌握度聚合 (section_id={section_id})")
            section_mastery, is_section_completed = await self._update_section_mastery(
                user_id, section_id, chapter_id, course_id
            )
            logger.info(f"[BKT] │ 小节掌握度 = {section_mastery * 100:.1f}%")
            logger.info(
                f"[BKT] │ 小节状态: {'[OK] 已完成' if is_section_completed else '学习中'}"
            )
            logger.info("[BKT] └─────────────────────────────────────────────────")

        # Step 6: 更新章节聚合掌握度（由所有小节聚合）
        chapter_mastery = 0.0
        is_chapter_completed = False

        if chapter_id:
            logger.info("[BKT] ┌─────────────────────────────────────────────────")
            logger.info(f"[BKT] │ 章节掌握度聚合 (chapter_id={chapter_id})")
            chapter_mastery, is_chapter_completed = await self._update_chapter_mastery(
                user_id, chapter_id, course_id
            )
            logger.info(f"[BKT] │ 章节掌握度 = {chapter_mastery * 100:.1f}%")
            logger.info(
                f"[BKT] │ 章节状态: {'[OK] 已完成' if is_chapter_completed else '学习中'}"
            )
            logger.info("[BKT] └─────────────────────────────────────────────────")

        # Step 7: 更新课程聚合掌握度（由所有章节聚合）
        course_mastery = 0.0
        is_course_completed = False

        if course_id:
            course_mastery, is_course_completed = await self._update_course_mastery(
                user_id, course_id
            )

        await self.db.commit()

        logger.info(
            "[BKT] ╔══════════════════════════════════════════════════════════════════"
        )
        logger.info(
            "[BKT] ║                    BKT 答题处理完成                              ║"
        )
        logger.info(
            "[BKT] ╠══════════════════════════════════════════════════════════════════"
        )
        logger.info(f"[BKT] ║ 计入掌握度: {counted}")
        logger.info(f"[BKT] ║ 小节掌握度: {section_mastery * 100:.1f}%")
        logger.info(f"[BKT] ║ 章节掌握度: {chapter_mastery * 100:.1f}%")
        logger.info(f"[BKT] ║ 课程掌握度: {course_mastery * 100:.1f}%")
        logger.info(
            "[BKT] ╚══════════════════════════════════════════════════════════════════"
        )

        return {
            "counted": counted,
            "not_counted_reason": not_counted_reason if not counted else None,
            "mastery_changes": mastery_changes,
            "section_mastery": section_mastery,
            "chapter_mastery": chapter_mastery,
            "course_mastery": course_mastery,
            "is_section_completed": is_section_completed,
            "is_chapter_completed": is_chapter_completed,
            "is_course_completed": is_course_completed,
        }

    async def _check_should_count(
        self,
        user_id: str,
        question_source: str,
        question_id: int,
        knowledge_points: List[str],
        section_id: Optional[int] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        检查是否应该计入掌握度

        防刷分规则（适配 AI 生成题目场景）：
        1. 同一题只有首次作答计入（虽然 AI 生成新题，但仍有去重需求）
        2. 每小节每知识点最多计入 N 次
        3. 每小时每知识点最多计入 M 次
        4. 答题时间过短不计入（< MIN_ANSWER_TIME_SECONDS）

        Returns:
            (should_count, reason_if_not)
        """
        # 规则1：检查是否已答过此题（且计入了掌握度）
        existing = await self.db.execute(
            select(AnswerHistory).where(
                AnswerHistory.user_id == user_id,
                AnswerHistory.question_source == question_source,
                AnswerHistory.question_id == question_id,
                AnswerHistory.counted_for_mastery,
            )
        )
        if existing.scalar_one_or_none():
            logger.info(f"[BKT] 题目 {question_id} 已答过且计入掌握度，本次不计入")
            return False, "duplicate_question"

        # 规则2：答题时间过短检测
        if (
            time_spent_seconds is not None
            and time_spent_seconds < self.MIN_ANSWER_TIME_SECONDS
        ):
            logger.info(
                f"[BKT] 答题时间过短 ({time_spent_seconds}s < {self.MIN_ANSWER_TIME_SECONDS}s)，不计入"
            )
            return False, "answer_too_fast"

        # 规则3：每小节每知识点限制（如果有小节信息）
        # 注意：由于 AnswerHistory 没有单独的知识点字段，我们通过 KnowledgePointMastery 来查询
        if section_id and knowledge_points:
            for kp in knowledge_points:
                # 通过 KnowledgePointMastery 查询该小节内该知识点的计入次数
                # 获取该知识点在小节内的记录
                kp_mastery = await self.db.execute(
                    select(KnowledgePointMastery).where(
                        KnowledgePointMastery.user_id == user_id,
                        KnowledgePointMastery.knowledge_point == kp,
                        KnowledgePointMastery.section_id == section_id,
                    )
                )
                kp_record = kp_mastery.scalar_one_or_none()
                if (
                    kp_record
                    and kp_record.total_attempts >= self.MAX_KP_ATTEMPTS_PER_SECTION
                ):
                    logger.info(
                        f"[BKT] 小节 {section_id} 内知识点 '{kp}' 已计入 {kp_record.total_attempts} 次，触发限制"
                    )
                    return False, "section_rate_limited"

        # 规则4：每小时知识点频率限制
        # 检查每个知识点在一小时内的计入次数
        if knowledge_points:
            for kp in knowledge_points:
                # 通过 KnowledgePointMastery 的 last_practiced_at 判断
                # 由于没有每小时单独的计数，我们用更宽松的限制
                kp_mastery = await self.db.execute(
                    select(KnowledgePointMastery).where(
                        KnowledgePointMastery.user_id == user_id,
                        KnowledgePointMastery.knowledge_point == kp,
                    )
                )
                kp_record = kp_mastery.scalar_one_or_none()
                # 如果最近有练习且尝试次数很高，才限制
                # 这里用 total_attempts 作为简单判断，因为每小时限制主要用于防止刷分
                if (
                    kp_record
                    and kp_record.total_attempts >= self.MAX_KP_ATTEMPTS_PER_HOUR
                ):
                    logger.info(
                        f"[BKT] 知识点 '{kp}' 总计入次数 {kp_record.total_attempts} 达到上限，触发限制"
                    )
                    return False, "rate_limited"

        return True, None

    async def _get_or_create_kp_mastery(
        self,
        user_id: str,
        knowledge_point: str,
        course_id: Optional[int],
        chapter_id: Optional[int],
        section_id: Optional[int] = None,
    ) -> KnowledgePointMastery:
        """
        获取或创建知识点掌握记录

        注意：同一知识点可能出现在多个小节中，因此我们需要：
        1. 如果有 section_id，优先按 section_id 查找/创建
        2. 如果没有 section_id，则按 chapter_id 查找/创建

        这样可以确保小节级的掌握度聚合正确工作。
        """
        if section_id:
            # 有小节信息时，按小节查找
            result = await self.db.execute(
                select(KnowledgePointMastery).where(
                    KnowledgePointMastery.user_id == user_id,
                    KnowledgePointMastery.knowledge_point == knowledge_point,
                    KnowledgePointMastery.section_id == section_id,
                )
            )
        else:
            # 没有小节信息时，按章节查找（兼容旧逻辑）
            result = await self.db.execute(
                select(KnowledgePointMastery).where(
                    KnowledgePointMastery.user_id == user_id,
                    KnowledgePointMastery.knowledge_point == knowledge_point,
                )
            )
        kp_mastery = result.scalar_one_or_none()

        if not kp_mastery:
            kp_mastery = KnowledgePointMastery(
                user_id=user_id,
                knowledge_point=knowledge_point,
                course_id=course_id,
                chapter_id=chapter_id,
                section_id=section_id,
                p_l=DEFAULT_P_L0,  # 初始掌握概率
            )
            self.db.add(kp_mastery)
            await self.db.flush()

        return kp_mastery

    async def _record_answer_history(
        self,
        user_id: str,
        question_source: str,
        question_id: int,
        is_correct: bool,
        knowledge_points: List[str],
        counted: bool,
        not_counted_reason: Optional[str],
        course_id: Optional[int],
        chapter_id: Optional[int],
        user_answer: Optional[str],
        time_spent_seconds: Optional[int],
        p_l_before: float,
        p_l_after: float,
    ) -> AnswerHistory:
        """记录答题历史"""
        exercise_key = (
            f"{question_source}-{course_id or 0}-{chapter_id or 0}-{question_id}"
        )

        history = AnswerHistory(
            user_id=user_id,
            question_source=question_source,
            question_id=question_id,
            exercise_key=exercise_key,
            course_id=course_id,
            chapter_id=chapter_id,
            is_correct=is_correct,
            user_answer=user_answer,
            time_spent_seconds=time_spent_seconds,
            p_l_before=p_l_before,
            p_l_after=p_l_after,
            knowledge_points_updated=knowledge_points,
            counted_for_mastery=counted,
            not_counted_reason=not_counted_reason,
        )
        self.db.add(history)
        return history

    async def _update_section_mastery(
        self,
        user_id: str,
        section_id: int,
        chapter_id: Optional[int],
        course_id: Optional[int],
    ) -> Tuple[float, bool]:
        """
        更新小节聚合掌握度

        小节掌握度 = 该小节内所有知识点的平均 P(L)

        重要：
        - 使用 section_knowledge_points 表获取小节的所有知识点
        - 对于用户没有练习过的知识点，使用初始掌握度 0.15
        - 这样确保小节掌握度正确反映小节的整体掌握情况

        Returns:
            (聚合掌握度, 是否完成)
        """
        from app.models.section_knowledge_point import SectionKnowledgePoint

        # Step 1: 获取小节的所有知识点（从 section_knowledge_points 表）
        kp_list_result = await self.db.execute(
            select(SectionKnowledgePoint).where(
                SectionKnowledgePoint.section_id == section_id,
                SectionKnowledgePoint.is_active,
            )
        )
        all_kp_list = kp_list_result.scalars().all()

        logger.info(f"[BKT] │ 小节 {section_id} 知识点总数: {len(all_kp_list)}")

        # 获取或创建 SectionMastery
        section_mastery = await self._get_or_create_section_mastery(
            user_id, section_id, chapter_id, course_id
        )

        if not all_kp_list:
            # 小节没有定义知识点
            section_mastery.bkt_aggregated_p_l = 0.15
            section_mastery.mastery_score = 15.0
            section_mastery.knowledge_points_count = 0
            section_mastery.mastered_points_count = 0
            logger.info("[BKT] │ 小节无知识点定义，使用默认值 15%")
            return 0.15, False

        # Step 2: 获取用户已练习的知识点的掌握状态
        result = await self.db.execute(
            select(KnowledgePointMastery).where(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.section_id == section_id,
            )
        )
        user_kp_masteries = result.scalars().all()
        user_kp_map = {kp.knowledge_point: kp for kp in user_kp_masteries}

        logger.info(f"[BKT] │ 用户已练习知识点数: {len(user_kp_masteries)}")

        # Step 3: 计算所有知识点的掌握度
        # 对于未练习的知识点，使用初始掌握度 DEFAULT_P_L0
        total_p_l = 0.0
        mastered_count = 0

        for skp in all_kp_list:
            kp_name = skp.name
            if kp_name in user_kp_map:
                # 用户已练习过该知识点
                kp_mastery = user_kp_map[kp_name]
                p_l = kp_mastery.p_l
                status = (
                    "[OK] 已掌握" if kp_mastery.p_l >= MASTERY_THRESHOLD else "学习中"
                )
                logger.info(
                    f"[BKT] │   知识点 '{kp_name}': P(L)={p_l:.4f} ({status}, 已练习)"
                )
            else:
                # 用户未练习过该知识点，使用初始掌握度
                p_l = DEFAULT_P_L0
                logger.info(f"[BKT] │   知识点 '{kp_name}': P(L)={p_l:.4f} (未练习)")

            total_p_l += p_l
            if p_l >= MASTERY_THRESHOLD:
                mastered_count += 1

        # Step 4: 计算平均掌握度
        avg_p_l = total_p_l / len(all_kp_list)

        logger.info(f"[BKT] │ 总 P(L) = {total_p_l:.4f}, 知识点数 = {len(all_kp_list)}")
        logger.info(f"[BKT] │ 平均 P(L) = {avg_p_l:.4f} ({avg_p_l * 100:.2f}%)")
        logger.info(f"[BKT] │ 已掌握知识点: {mastered_count} / {len(all_kp_list)}")

        # 更新小节掌握度
        section_mastery.bkt_aggregated_p_l = avg_p_l
        section_mastery.mastery_score = avg_p_l * 100
        section_mastery.knowledge_points_count = len(all_kp_list)
        section_mastery.mastered_points_count = mastered_count
        section_mastery.last_attempt_at = utc_now()

        if not section_mastery.first_attempt_at:
            section_mastery.first_attempt_at = utc_now()

        # 判断是否完成：所有知识点都掌握
        is_completed = mastered_count == len(all_kp_list)
        section_mastery.is_completed = is_completed

        if is_completed and not section_mastery.completed_at:
            section_mastery.completed_at = utc_now()
            logger.info(f"[BKT] [*] 小节 {section_id} 完成！所有知识点已掌握！")

        return avg_p_l, is_completed

    async def _get_or_create_section_mastery(
        self,
        user_id: str,
        section_id: int,
        chapter_id: Optional[int],
        course_id: Optional[int],
    ) -> SectionMastery:
        """获取或创建小节掌握记录"""
        result = await self.db.execute(
            select(SectionMastery).where(
                SectionMastery.user_id == user_id,
                SectionMastery.section_id == section_id,
            )
        )
        section_mastery = result.scalar_one_or_none()

        if not section_mastery:
            section_mastery = SectionMastery(
                user_id=user_id,
                section_id=section_id,
                chapter_id=chapter_id,
                first_attempt_at=utc_now(),
            )
            self.db.add(section_mastery)
            await self.db.flush()

        return section_mastery

    async def _update_chapter_mastery(
        self,
        user_id: str,
        chapter_id: int,
        course_id: Optional[int],
    ) -> Tuple[float, bool]:
        """
        更新章节聚合掌握度

        章节掌握度 = Σ(小节掌握度 × 小节知识点数) / 总知识点数

        重要：
        - 未开始测试的小节掌握度为 0%
        - 开始测试后的小节才有实际掌握度（初始15%，随答题变化）

        Returns:
            (聚合掌握度, 是否完成)
        """
        from app.models.section_knowledge_point import SectionKnowledgePoint
        from app.models.section import Section

        # Step 1: 获取章节内所有小节
        sections_result = await self.db.execute(
            select(Section).where(Section.chapter_id == chapter_id)
        )
        sections = sections_result.scalars().all()
        section_ids = [s.id for s in sections]

        # Step 2: 获取每个小节的知识点数量
        kp_count_result = await self.db.execute(
            select(
                SectionKnowledgePoint.section_id,
                func.count(SectionKnowledgePoint.id).label("kp_count"),
            )
            .where(
                SectionKnowledgePoint.section_id.in_(section_ids),
                SectionKnowledgePoint.is_active,
            )
            .group_by(SectionKnowledgePoint.section_id)
        )
        section_kp_counts = {
            row.section_id: row.kp_count for row in kp_count_result.all()
        }

        # 计算章节总知识点数
        total_kp_count = sum(section_kp_counts.values())
        logger.info(f"[BKT] │ 章节 {chapter_id} 总知识点数: {total_kp_count}")
        logger.info(f"[BKT] │ 各小节知识点数: {section_kp_counts}")

        # 获取或创建 ChapterMastery
        chapter_mastery = await self._get_or_create_chapter_mastery(
            user_id, chapter_id, course_id
        )

        if total_kp_count == 0:
            chapter_mastery.bkt_aggregated_p_l = 0.0
            chapter_mastery.mastery_score = 0.0
            chapter_mastery.knowledge_points_count = 0
            chapter_mastery.mastered_points_count = 0
            logger.info("[BKT] │ 章节无知识点，使用默认值 0%")
            return 0.0, False

        # Step 3: 获取每个小节的掌握度
        # 只有开始了测试（有 first_attempt_at）的小节才有实际掌握度
        section_mastery_result = await self.db.execute(
            select(SectionMastery).where(
                SectionMastery.user_id == user_id,
                SectionMastery.section_id.in_(section_ids),
            )
        )
        section_masteries = section_mastery_result.scalars().all()
        section_mastery_map = {sm.section_id: sm for sm in section_masteries}

        # Step 4: 计算加权平均掌握度
        # 章节掌握度 = Σ(小节掌握度 × 小节知识点数) / 总知识点数
        weighted_sum = 0.0
        started_sections = 0

        for section_id in section_ids:
            kp_count = section_kp_counts.get(section_id, 0)
            if kp_count == 0:
                continue

            sm = section_mastery_map.get(section_id)
            if sm and sm.first_attempt_at:
                # 小节已开始测试，使用实际掌握度
                section_p_l = sm.bkt_aggregated_p_l
                started_sections += 1
                logger.info(
                    f"[BKT] │   小节 {section_id}: P(L)={section_p_l:.4f} (已开始, {kp_count}个知识点)"
                )
            else:
                # 小节未开始，掌握度为 0
                section_p_l = 0.0
                logger.info(
                    f"[BKT] │   小节 {section_id}: P(L)={section_p_l:.4f} (未开始, {kp_count}个知识点)"
                )

            weighted_sum += section_p_l * kp_count

        # 章节平均掌握度
        avg_p_l = weighted_sum / total_kp_count if total_kp_count > 0 else 0.0

        logger.info(f"[BKT] │ 加权和 = {weighted_sum:.4f}, 总知识点 = {total_kp_count}")
        logger.info(f"[BKT] │ 章节掌握度 = {avg_p_l:.4f} ({avg_p_l * 100:.1f}%)")
        logger.info(f"[BKT] │ 已开始小节数: {started_sections} / {len(sections)}")

        # Step 5: 计算已掌握知识点数（用于统计）
        # 需要从知识点级别统计
        result = await self.db.execute(
            select(KnowledgePointMastery).where(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.chapter_id == chapter_id,
            )
        )
        kp_masteries = result.scalars().all()
        mastered_count = sum(1 for kp in kp_masteries if kp.p_l >= MASTERY_THRESHOLD)

        # 更新章节掌握度
        chapter_mastery.bkt_aggregated_p_l = avg_p_l
        chapter_mastery.mastery_score = avg_p_l * 100
        chapter_mastery.knowledge_points_count = total_kp_count
        chapter_mastery.mastered_points_count = mastered_count

        from app.services.chapter_mastery import ChapterMasteryService

        chapter_mastery.mastery_level = ChapterMasteryService(None).get_mastery_level(
            avg_p_l * 100
        )
        chapter_mastery.last_practiced_at = utc_now()

        # 判断是否完成：所有知识点都掌握（需要所有小节都开始并掌握）
        is_completed = (
            mastered_count == total_kp_count
            and total_kp_count > 0
            and started_sections == len(sections)
        )

        if is_completed and not chapter_mastery.mastered_at:
            chapter_mastery.mastered_at = utc_now()
            logger.info(
                f"[BKT] [*] 章节 {chapter_id} 完成！所有 {total_kp_count} 个知识点已掌握！"
            )

        return avg_p_l, is_completed

    async def _get_or_create_chapter_mastery(
        self,
        user_id: str,
        chapter_id: int,
        course_id: Optional[int],
    ) -> ChapterMastery:
        """获取或创建章节掌握记录"""
        result = await self.db.execute(
            select(ChapterMastery).where(
                ChapterMastery.user_id == user_id,
                ChapterMastery.chapter_id == chapter_id,
            )
        )
        chapter_mastery = result.scalar_one_or_none()

        if not chapter_mastery:
            chapter_mastery = ChapterMastery(
                user_id=user_id,
                chapter_id=chapter_id,
                course_id=course_id or 0,
                first_practiced_at=utc_now(),
            )
            self.db.add(chapter_mastery)
            await self.db.flush()

        return chapter_mastery

    # ========== 查询方法 ==========

    async def get_knowledge_point_status(
        self,
        user_id: str,
        knowledge_point: str,
    ) -> Optional[KnowledgePointMastery]:
        """获取单个知识点状态"""
        result = await self.db.execute(
            select(KnowledgePointMastery).where(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.knowledge_point == knowledge_point,
            )
        )
        return result.scalar_one_or_none()

    async def get_chapter_knowledge_points(
        self,
        user_id: str,
        chapter_id: int,
    ) -> List[KnowledgePointMastery]:
        """获取章节内所有知识点状态"""
        result = await self.db.execute(
            select(KnowledgePointMastery).where(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.chapter_id == chapter_id,
            )
        )
        return list(result.scalars().all())

    async def get_weak_knowledge_points(
        self,
        user_id: str,
        chapter_id: Optional[int] = None,
        threshold: float = 0.5,
        limit: int = 5,
    ) -> List[KnowledgePointMastery]:
        """
        获取薄弱知识点

        Args:
            user_id: 用户ID
            chapter_id: 章节ID（可选，不指定则查询所有）
            threshold: 掌握度阈值，低于此值为薄弱
            limit: 返回数量限制

        Returns:
            薄弱知识点列表，按掌握度升序排列
        """
        query = select(KnowledgePointMastery).where(
            KnowledgePointMastery.user_id == user_id,
            KnowledgePointMastery.p_l < threshold,
        )

        if chapter_id:
            query = query.where(KnowledgePointMastery.chapter_id == chapter_id)

        query = query.order_by(KnowledgePointMastery.p_l.asc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_mastery_summary(
        self,
        user_id: str,
        chapter_id: int,
    ) -> Dict:
        """
        获取章节掌握度摘要

        Returns:
            {
                "total_knowledge_points": int,
                "mastered_knowledge_points": int,
                "average_p_l": float,
                "mastery_score": float,
                "is_completed": bool,
                "weak_points": List[str],
            }
        """
        kp_masteries = await self.get_chapter_knowledge_points(user_id, chapter_id)

        if not kp_masteries:
            return {
                "total_knowledge_points": 0,
                "mastered_knowledge_points": 0,
                "average_p_l": 0.0,
                "mastery_score": 0.0,
                "is_completed": False,
                "weak_points": [],
            }

        total = len(kp_masteries)
        mastered = sum(1 for kp in kp_masteries if kp.is_mastered)
        avg_p_l = sum(kp.p_l for kp in kp_masteries) / total
        weak_points = [kp.knowledge_point for kp in kp_masteries if kp.p_l < 0.5]

        return {
            "total_knowledge_points": total,
            "mastered_knowledge_points": mastered,
            "average_p_l": avg_p_l,
            "mastery_score": avg_p_l * 100,
            "is_completed": mastered == total,
            "weak_points": weak_points,
        }

    async def check_section_completion(
        self,
        user_id: str,
        section_knowledge_points: List[str],
    ) -> Tuple[bool, float]:
        """
        检查小节是否完成

        Args:
            user_id: 用户ID
            section_knowledge_points: 小节涉及的知识点列表

        Returns:
            (是否完成, 平均掌握概率)
        """
        if not section_knowledge_points:
            return False, 0.0

        # 获取所有知识点的掌握状态
        p_l_values = []
        for kp_name in section_knowledge_points:
            kp_mastery = await self.get_knowledge_point_status(user_id, kp_name)
            if kp_mastery:
                p_l_values.append(kp_mastery.p_l)
            else:
                p_l_values.append(DEFAULT_P_L0)  # 未学过，初始概率

        avg_p_l = sum(p_l_values) / len(p_l_values)
        is_completed = all(p >= MASTERY_THRESHOLD for p in p_l_values)

        return is_completed, avg_p_l

    # ========== 课程聚合方法 ==========

    async def _update_course_mastery(
        self,
        user_id: str,
        course_id: int,
    ) -> Tuple[float, bool]:
        """
        更新课程聚合掌握度

        课程掌握度 = Σ(章节掌握度 × 章节知识点数) / 总知识点数

        重要：
        - 未开始测试的小节掌握度为 0%
        - 开始测试后的小节才有实际掌握度（初始15%，随答题变化）

        Returns:
            (聚合掌握度, 是否完成)
        """
        from app.models.section_knowledge_point import SectionKnowledgePoint
        from app.models.section import Section
        from app.models.chapter import Chapter

        # Step 1: 获取课程内所有章节
        chapters_result = await self.db.execute(
            select(Chapter).where(Chapter.course_id == course_id)
        )
        all_chapters = chapters_result.scalars().all()
        chapter_ids = [ch.id for ch in all_chapters]
        chapters_count = len(all_chapters)

        # Step 2: 获取所有章节的小节
        sections_result = await self.db.execute(
            select(Section).where(Section.chapter_id.in_(chapter_ids))
        )
        sections = sections_result.scalars().all()
        section_ids = [s.id for s in sections]

        # Step 3: 获取每个章节的知识点总数
        # 先获取每个小节的知识点数
        kp_count_result = await self.db.execute(
            select(
                SectionKnowledgePoint.section_id,
                func.count(SectionKnowledgePoint.id).label("kp_count"),
            )
            .where(
                SectionKnowledgePoint.section_id.in_(section_ids),
                SectionKnowledgePoint.is_active,
            )
            .group_by(SectionKnowledgePoint.section_id)
        )
        section_kp_counts = {
            row.section_id: row.kp_count for row in kp_count_result.all()
        }

        # 构建小节到章节的映射，并计算每章的知识点数
        section_to_chapter = {s.id: s.chapter_id for s in sections}
        chapter_kp_counts = {}
        for section_id, kp_count in section_kp_counts.items():
            chapter_id = section_to_chapter.get(section_id)
            if chapter_id:
                chapter_kp_counts[chapter_id] = (
                    chapter_kp_counts.get(chapter_id, 0) + kp_count
                )

        # 计算课程总知识点数
        total_kp_count = sum(chapter_kp_counts.values())

        # 获取或创建 CourseMastery
        course_mastery = await self._get_or_create_course_mastery(user_id, course_id)

        if total_kp_count == 0:
            course_mastery.bkt_aggregated_p_l = 0.0
            course_mastery.mastery_score = 0.0
            course_mastery.knowledge_points_count = 0
            course_mastery.mastered_points_count = 0
            course_mastery.chapters_count = chapters_count
            course_mastery.completed_chapters_count = 0
            return 0.0, False

        # Step 4: 获取每个小节的掌握度
        section_mastery_result = await self.db.execute(
            select(SectionMastery).where(
                SectionMastery.user_id == user_id,
                SectionMastery.section_id.in_(section_ids),
            )
        )
        section_masteries = section_mastery_result.scalars().all()
        section_mastery_map = {sm.section_id: sm for sm in section_masteries}

        # Step 5: 计算每个章节的掌握度（加权平均）
        from collections import defaultdict

        chapter_sections = defaultdict(list)
        for s in sections:
            chapter_sections[s.chapter_id].append(s)

        chapter_mastery_map = {}
        for chapter_id in chapter_ids:
            ch_kp_count = chapter_kp_counts.get(chapter_id, 0)
            ch_sections_list = chapter_sections.get(chapter_id, [])

            if ch_kp_count == 0:
                chapter_mastery_map[chapter_id] = 0.0
                continue

            # 计算章节加权掌握度
            ch_weighted_sum = 0.0
            for s in ch_sections_list:
                s_kp_count = section_kp_counts.get(s.id, 0)
                if s_kp_count == 0:
                    continue

                sm = section_mastery_map.get(s.id)
                if sm and sm.first_attempt_at:
                    # 小节已开始测试，使用实际掌握度
                    section_p_l = sm.bkt_aggregated_p_l
                else:
                    # 小节未开始，掌握度为 0
                    section_p_l = 0.0

                ch_weighted_sum += section_p_l * s_kp_count

            chapter_mastery_map[chapter_id] = ch_weighted_sum / ch_kp_count

        # Step 6: 计算课程加权平均掌握度
        weighted_sum = 0.0
        started_chapters = 0

        for chapter_id in chapter_ids:
            kp_count = chapter_kp_counts.get(chapter_id, 0)
            if kp_count == 0:
                continue

            chapter_p_l = chapter_mastery_map.get(chapter_id, 0.0)
            if chapter_p_l > 0:
                started_chapters += 1
                logger.info(
                    f"[BKT] │   章节 {chapter_id}: P(L)={chapter_p_l:.4f} (已开始, {kp_count}个知识点)"
                )
            else:
                logger.info(
                    f"[BKT] │   章节 {chapter_id}: P(L)={chapter_p_l:.4f} (未开始, {kp_count}个知识点)"
                )

            weighted_sum += chapter_p_l * kp_count

        # 课程平均掌握度
        avg_p_l = weighted_sum / total_kp_count if total_kp_count > 0 else 0.0

        logger.info(f"[BKT] │ 加权和 = {weighted_sum:.4f}, 总知识点 = {total_kp_count}")
        logger.info(f"[BKT] │ 课程掌握度 = {avg_p_l:.4f} ({avg_p_l * 100:.1f}%)")
        logger.info(f"[BKT] │ 已开始章节数: {started_chapters} / {chapters_count}")

        # Step 7: 计算已完成章节数和已掌握知识点数
        # 获取 ChapterMastery 记录
        cm_result = await self.db.execute(
            select(ChapterMastery).where(
                ChapterMastery.user_id == user_id,
                ChapterMastery.chapter_id.in_(chapter_ids),
            )
        )
        chapter_masteries = cm_result.scalars().all()
        completed_chapters_count = sum(
            1 for cm in chapter_masteries if cm.mastered_at is not None
        )

        # 获取已掌握知识点数
        kp_result = await self.db.execute(
            select(KnowledgePointMastery).where(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.course_id == course_id,
            )
        )
        kp_masteries = kp_result.scalars().all()
        mastered_count = sum(1 for kp in kp_masteries if kp.p_l >= MASTERY_THRESHOLD)

        # 更新课程掌握度
        course_mastery.bkt_aggregated_p_l = avg_p_l
        course_mastery.mastery_score = avg_p_l * 100
        course_mastery.knowledge_points_count = total_kp_count
        course_mastery.mastered_points_count = mastered_count
        course_mastery.chapters_count = chapters_count
        course_mastery.completed_chapters_count = completed_chapters_count
        course_mastery.last_practiced_at = utc_now()

        if not course_mastery.first_practiced_at:
            course_mastery.first_practiced_at = utc_now()

        # 判断是否完成：所有知识点都掌握（需要所有章节都开始并掌握）
        is_completed = (
            mastered_count == total_kp_count
            and total_kp_count > 0
            and started_chapters == chapters_count
        )
        course_mastery.is_completed = is_completed

        if is_completed and not course_mastery.completed_at:
            course_mastery.completed_at = utc_now()
            logger.info(
                f"[BKT] 课程 {course_id} 完成！所有 {total_kp_count} 个知识点已掌握！"
            )

        return avg_p_l, is_completed

    async def _get_or_create_course_mastery(
        self,
        user_id: str,
        course_id: int,
    ) -> CourseMastery:
        """获取或创建课程掌握记录"""
        result = await self.db.execute(
            select(CourseMastery).where(
                CourseMastery.user_id == user_id,
                CourseMastery.course_id == course_id,
            )
        )
        course_mastery = result.scalar_one_or_none()

        if not course_mastery:
            course_mastery = CourseMastery(
                user_id=user_id,
                course_id=course_id,
                first_practiced_at=utc_now(),
            )
            self.db.add(course_mastery)
            await self.db.flush()

        return course_mastery

    # ========== 课程级查询方法 ==========

    async def get_course_mastery(
        self,
        user_id: str,
        course_id: int,
    ) -> Optional[CourseMastery]:
        """获取课程掌握度"""
        result = await self.db.execute(
            select(CourseMastery).where(
                CourseMastery.user_id == user_id,
                CourseMastery.course_id == course_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_course_mastery_summary(
        self,
        user_id: str,
        course_id: int,
    ) -> Dict:
        """
        获取课程掌握度摘要

        计算逻辑：
        1. 小节掌握度：未开始测试 → 0%，开始测试后 → BKT实际值（初始15%）
        2. 章节掌握度 = Σ(小节掌握度 × 小节知识点数) / 章节总知识点数
        3. 课程掌握度 = Σ(章节掌握度 × 章节知识点数) / 课程总知识点数

        Returns:
            {
                "mastery_score": float,
                "progress_percentage": float,
                "chapters_count": int,
                "completed_chapters": int,
                "is_completed": bool,
                "chapters": List[Dict],
            }
        """
        from app.models.section_knowledge_point import SectionKnowledgePoint
        from app.models.section_mastery import SectionMastery
        from app.models.section import Section
        from app.models.chapter import Chapter

        # Step 1: 获取课程内所有章节
        chapters_result = await self.db.execute(
            select(Chapter).where(Chapter.course_id == course_id)
        )
        all_chapters = chapters_result.scalars().all()
        chapters_count = len(all_chapters)

        logger.info(
            f"[BKT] get_course_mastery_summary: course_id={course_id}, chapters_count={chapters_count}"
        )

        # Step 2: 获取所有章节的小节
        chapter_ids = [ch.id for ch in all_chapters]
        sections_result = await self.db.execute(
            select(Section).where(Section.chapter_id.in_(chapter_ids))
        )
        sections = sections_result.scalars().all()
        section_ids = [s.id for s in sections]

        # Step 3: 获取每个小节的知识点数量
        kp_count_result = await self.db.execute(
            select(
                SectionKnowledgePoint.section_id,
                func.count(SectionKnowledgePoint.id).label("kp_count"),
            )
            .where(
                SectionKnowledgePoint.section_id.in_(section_ids),
                SectionKnowledgePoint.is_active,
            )
            .group_by(SectionKnowledgePoint.section_id)
        )
        section_kp_counts = {
            row.section_id: row.kp_count for row in kp_count_result.all()
        }

        # Step 4: 获取每个小节的掌握度（已开始测试的）
        section_mastery_result = await self.db.execute(
            select(SectionMastery).where(
                SectionMastery.user_id == user_id,
                SectionMastery.section_id.in_(section_ids),
            )
        )
        section_masteries = section_mastery_result.scalars().all()
        section_mastery_map = {sm.section_id: sm for sm in section_masteries}

        # Step 5: 构建小节到章节的映射
        section_to_chapter = {s.id: s.chapter_id for s in sections}

        # Step 6: 计算每个章节的知识点总数
        chapter_kp_counts = {}
        for section_id, kp_count in section_kp_counts.items():
            chapter_id = section_to_chapter.get(section_id)
            if chapter_id:
                chapter_kp_counts[chapter_id] = (
                    chapter_kp_counts.get(chapter_id, 0) + kp_count
                )

        total_kp_count = sum(chapter_kp_counts.values())
        logger.info(
            f"[BKT] get_course_mastery_summary: 课程总知识点数={total_kp_count}"
        )

        # Step 7: 计算各章节掌握度（加权平均）
        from collections import defaultdict

        chapter_sections = defaultdict(list)
        for s in sections:
            chapter_sections[s.chapter_id].append(s)

        chapters = []
        completed_chapters = 0
        course_weighted_sum = 0.0

        for chapter in all_chapters:
            ch_kp_count = chapter_kp_counts.get(chapter.id, 0)
            ch_sections_list = chapter_sections.get(chapter.id, [])

            if ch_kp_count == 0:
                chapters.append(
                    {
                        "chapter_id": chapter.id,
                        "mastery_score": 0.0,
                        "is_completed": False,
                    }
                )
                continue

            # 计算章节加权掌握度 = Σ(小节掌握度 × 小节知识点数) / 章节总知识点数
            ch_weighted_sum = 0.0
            ch_started_sections = 0
            ch_mastered_kps = 0

            for s in ch_sections_list:
                s_kp_count = section_kp_counts.get(s.id, 0)
                if s_kp_count == 0:
                    continue

                sm = section_mastery_map.get(s.id)
                if sm and sm.first_attempt_at:
                    # 小节已开始测试，使用实际掌握度
                    section_p_l = sm.bkt_aggregated_p_l
                    ch_started_sections += 1
                    if sm.is_completed:
                        ch_mastered_kps += s_kp_count
                else:
                    # 小节未开始，掌握度为 0
                    section_p_l = 0.0

                ch_weighted_sum += section_p_l * s_kp_count

            # 章节平均掌握度
            ch_avg_p_l = ch_weighted_sum / ch_kp_count
            ch_mastery_score = ch_avg_p_l * 100

            # 判断是否完成：所有小节都开始且掌握
            is_completed = (
                ch_started_sections
                == len(
                    [s for s in ch_sections_list if section_kp_counts.get(s.id, 0) > 0]
                )
                and ch_avg_p_l >= MASTERY_THRESHOLD
            )

            if is_completed:
                completed_chapters += 1

            chapters.append(
                {
                    "chapter_id": chapter.id,
                    "mastery_score": round(ch_mastery_score, 2),
                    "is_completed": is_completed,
                }
            )

            # 累加到课程加权平均
            course_weighted_sum += ch_avg_p_l * ch_kp_count

        # 课程平均掌握度
        avg_p_l = course_weighted_sum / total_kp_count if total_kp_count > 0 else 0.0
        mastery_score = avg_p_l * 100

        # 计算已掌握知识点数（用于进度百分比）
        # 获取用户已学知识点的掌握状态
        mastery_result = await self.db.execute(
            select(KnowledgePointMastery).where(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.course_id == course_id,
            )
        )
        kp_masteries = mastery_result.scalars().all()
        mastered_count = sum(1 for kp in kp_masteries if kp.p_l >= MASTERY_THRESHOLD)

        # 进度百分比 = 已掌握知识点 / 总知识点
        progress_percentage = (
            (mastered_count / total_kp_count) * 100 if total_kp_count > 0 else 0.0
        )

        logger.info(
            f"[BKT] get_course_mastery_summary 课程整体: mastery_score={mastery_score:.2f}%, progress_percentage={progress_percentage:.2f}%"
        )

        if total_kp_count == 0:
            return {
                "mastery_score": 0.0,
                "progress_percentage": 0.0,
                "chapters_count": chapters_count,
                "completed_chapters": 0,
                "is_completed": False,
                "chapters": chapters,
            }

        return {
            "mastery_score": round(mastery_score, 2),
            "progress_percentage": round(progress_percentage, 2),
            "chapters_count": chapters_count,
            "completed_chapters": completed_chapters,
            "is_completed": mastered_count == total_kp_count,
            "chapters": chapters,
        }
