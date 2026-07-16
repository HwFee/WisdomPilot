"""
Learning Path Router

API endpoints for the dual learning path system:
- Mastery Path (精进之路): Chapter-based learning
- Challenge Path (挑战之路): Difficulty-based challenges
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.exercise import Exercise
from app.services.leaderboard_service import (
    get_arena_leaderboard_service,
    get_mastery_leaderboard_service,
)
from app.services.adaptive_recommendation import AdaptiveRecommendationService
from app.services.challenge_path import (
    ChallengeExerciseNotFoundError,
    ChallengeProgressService,
    ChallengeProgressNotFoundError,
    ChallengeSelectionService,
    ChallengeSubmissionService,
    JudgeUnavailableError,
    MissingChallengeTestCasesError,
    UnsupportedChallengeLanguageError,
)
from app.services.challenge_path.responses import (
    map_exercise_detail_response,
    map_exercise_summary,
    map_switch_response,
)
from app.schemas.exercise import ExerciseRecommendRequest


router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])


# ========== Schemas ==========


class MasteryOverviewResponse(BaseModel):
    """Response for mastery path overview"""

    course_id: int
    total_chapters: int
    mastered_chapters: int
    current_chapter: Optional[int]
    total_mastery_points: float
    avg_mastery: float
    chapters: list[dict]


class ChapterMasteryResponse(BaseModel):
    """Response for chapter mastery details"""

    chapter_id: int
    chapter_title: str
    mastery_score: float
    mastery_level: str
    accuracy_score: float
    consistency_score: float
    depth_score: float
    recency_score: float
    total_exercises: int
    correct_exercises: int
    can_advance: bool
    objectives_status: Optional[dict]


class ChallengeSessionResponse(BaseModel):
    """Response for challenge session"""

    session_id: str
    difficulty_level: int
    exercises: list[dict]
    time_limit: int
    score_multiplier: float
    status: str


class LeaderboardResponse(BaseModel):
    """Response for leaderboard"""

    leaderboard_type: str
    course_id: int
    entries: list[dict]
    user_rank: Optional[int]


# ========== Mastery Path Endpoints ==========


@router.get("/mastery/{course_id}/overview", response_model=MasteryOverviewResponse)
async def get_mastery_overview(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's mastery path overview for a course

    章节掌握度 = Σ(小节掌握度 × 小节知识点数) / 总知识点数
    小节掌握度：未开始测试 → 0%，开始测试后 → BKT实际值（初始15%）
    """
    from app.models.section_knowledge_point import SectionKnowledgePoint
    from app.models.section_mastery import SectionMastery
    from app.models.section import Section

    # Get all chapters for the course
    chapters_result = await db.execute(
        select(Chapter)
        .where(Chapter.course_id == course_id)
        .order_by(Chapter.order_index)
    )
    chapters = chapters_result.scalars().all()

    if not chapters:
        return MasteryOverviewResponse(
            course_id=course_id,
            total_chapters=0,
            mastered_chapters=0,
            current_chapter=None,
            total_mastery_points=0,
            avg_mastery=0,
            chapters=[],
        )

    chapter_ids = [ch.id for ch in chapters]

    # 获取所有章节的小节
    sections_result = await db.execute(
        select(Section).where(Section.chapter_id.in_(chapter_ids))
    )
    sections = sections_result.scalars().all()
    section_ids = [s.id for s in sections]

    # 构建小节到章节的映射
    section_to_chapter = {s.id: s.chapter_id for s in sections}

    # 获取每个小节的知识点数量
    kp_count_result = await db.execute(
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
    section_kp_counts = {row.section_id: row.kp_count for row in kp_count_result.all()}

    # 获取每个章节的知识点总数
    chapter_kp_counts = {}
    for section_id, kp_count in section_kp_counts.items():
        chapter_id = section_to_chapter.get(section_id)
        if chapter_id:
            chapter_kp_counts[chapter_id] = (
                chapter_kp_counts.get(chapter_id, 0) + kp_count
            )

    # 获取每个小节的掌握度（已开始测试的）
    section_mastery_result = await db.execute(
        select(SectionMastery).where(
            SectionMastery.user_id == current_user.id,
            SectionMastery.section_id.in_(section_ids),
        )
    )
    section_masteries = section_mastery_result.scalars().all()
    section_mastery_map = {sm.section_id: sm for sm in section_masteries}

    # 构建章节列表
    chapter_list = []
    total_mastery_points = 0
    total_kp_count = 0
    weighted_mastery_sum = 0
    mastered_count = 0
    current_chapter = None

    for ch in chapters:
        ch_kp_count = chapter_kp_counts.get(ch.id, 0)

        # Skip chapters with no knowledge points / sections
        if ch_kp_count == 0:
            continue

        # 计算章节加权掌握度 = Σ(小节掌握度 × 小节知识点数) / 章节总知识点数
        ch_weighted_sum = 0.0
        ch_started_sections = 0
        ch_total_sections = 0

        # 获取该章节的所有小节
        ch_sections = [s for s in sections if s.chapter_id == ch.id]

        for s in ch_sections:
            s_kp_count = section_kp_counts.get(s.id, 0)
            if s_kp_count == 0:
                continue

            ch_total_sections += 1
            sm = section_mastery_map.get(s.id)

            if sm and sm.first_attempt_at:
                # 小节已开始测试，使用实际掌握度
                section_p_l = sm.bkt_aggregated_p_l
                ch_started_sections += 1
            else:
                # 小节未开始，掌握度为 0
                section_p_l = 0.0

            ch_weighted_sum += section_p_l * s_kp_count

        # 章节平均掌握度
        ch_avg_p_l = ch_weighted_sum / ch_kp_count
        mastery_score = ch_avg_p_l * 100

        # 判断是否完成：所有小节都开始且掌握
        is_mastered = ch_started_sections == ch_total_sections and ch_avg_p_l >= 0.95

        # 章节等级
        if mastery_score >= 95:
            mastery_level = "精通"
        elif mastery_score >= 85:
            mastery_level = "熟练"
        elif mastery_score >= 70:
            mastery_level = "练习"
        elif mastery_score >= 50:
            mastery_level = "学习"
        else:
            mastery_level = "入门"

        total_mastery_points += mastery_score
        total_kp_count += ch_kp_count
        weighted_mastery_sum += ch_kp_count * mastery_score
        if is_mastered:
            mastered_count += 1

        # 找到第一个未完成的章节
        if current_chapter is None and not is_mastered:
            current_chapter = ch.order_index

        chapter_list.append(
            {
                "chapter_id": ch.id,
                "order_index": ch.order_index,
                "title": ch.title,
                "mastery_score": round(mastery_score, 2),
                "mastery_level": mastery_level,
                "can_advance": mastery_score >= 75,
            }
        )

    # 计算平均掌握度（按知识点数量加权）
    avg_mastery = weighted_mastery_sum / total_kp_count if total_kp_count > 0 else 0

    return MasteryOverviewResponse(
        course_id=course_id,
        total_chapters=len(chapters),
        mastered_chapters=mastered_count,
        current_chapter=current_chapter,
        total_mastery_points=round(total_mastery_points, 2),
        avg_mastery=round(avg_mastery, 2),
        chapters=chapter_list,
    )


@router.get(
    "/mastery/{course_id}/chapter/{chapter_id}", response_model=ChapterMasteryResponse
)
async def get_chapter_mastery(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed mastery info for a specific chapter"""
    from app.models.knowledge_point_mastery import (
        KnowledgePointMastery,
        MASTERY_THRESHOLD,
    )

    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Get knowledge point masteries for this chapter
    kp_result = await db.execute(
        select(KnowledgePointMastery).where(
            KnowledgePointMastery.user_id == current_user.id,
            KnowledgePointMastery.chapter_id == chapter_id,
        )
    )
    kp_masteries = kp_result.scalars().all()

    if not kp_masteries:
        # Return default values
        return ChapterMasteryResponse(
            chapter_id=chapter_id,
            chapter_title=chapter.title,
            mastery_score=0,
            mastery_level="入门",
            accuracy_score=0,
            consistency_score=0,
            depth_score=0,
            recency_score=0,
            total_exercises=0,
            correct_exercises=0,
            can_advance=False,
            objectives_status=None,
        )

    # Calculate from knowledge points
    avg_p_l = sum(kp.p_l for kp in kp_masteries) / len(kp_masteries)
    mastery_score = avg_p_l * 100
    mastered_kps = sum(1 for kp in kp_masteries if kp.p_l >= MASTERY_THRESHOLD)
    total_exercises = len(kp_masteries)
    correct_exercises = mastered_kps

    # Chapter level
    if mastery_score >= 95:
        mastery_level = "精通"
    elif mastery_score >= 85:
        mastery_level = "熟练"
    elif mastery_score >= 70:
        mastery_level = "练习"
    elif mastery_score >= 50:
        mastery_level = "学习"
    else:
        mastery_level = "入门"

    return ChapterMasteryResponse(
        chapter_id=chapter_id,
        chapter_title=chapter.title,
        mastery_score=round(mastery_score, 2),
        mastery_level=mastery_level,
        accuracy_score=round(mastery_score, 2),
        consistency_score=round(mastery_score, 2),
        depth_score=round(mastery_score, 2),
        recency_score=round(mastery_score, 2),
        total_exercises=total_exercises,
        correct_exercises=correct_exercises,
        can_advance=mastery_score >= 75,
        objectives_status=None,
    )


@router.post("/mastery/{course_id}/chapter/{chapter_id}/recommend")
async def recommend_mastery_exercises(
    course_id: int,
    chapter_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recommended exercises for mastery path (chapter-based)"""
    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Use adaptive recommendation with chapter_id and mastery path
    request = ExerciseRecommendRequest(
        chapter_id=chapter_id,
        learning_path="mastery",
        limit=limit,
    )

    service = AdaptiveRecommendationService(db)
    exercises = await service.get_recommendations(
        user=current_user,
        limit=limit,
        min_difficulty=1,
        max_difficulty=5,
        chapter_id=chapter_id,
        learning_path="mastery",
    )

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter.title,
        "learning_path": "mastery",
        "exercises": exercises,
    }


# ========== Leaderboard Endpoints ==========


@router.get("/leaderboard/{course_id}/mastery", response_model=LeaderboardResponse)
async def get_mastery_leaderboard(
    course_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mastery leaderboard for a course"""
    service = get_mastery_leaderboard_service(db)
    entries = await service.get_leaderboard(course_id, limit, offset)
    user_rank = await service.get_user_rank(current_user.id, course_id)

    return LeaderboardResponse(
        leaderboard_type="mastery",
        course_id=course_id,
        entries=entries,
        user_rank=user_rank,
    )


@router.get("/leaderboard/{course_id}/arena", response_model=LeaderboardResponse)
async def get_arena_leaderboard(
    course_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get arena leaderboard for a course"""
    service = get_arena_leaderboard_service(db)
    entries = await service.get_leaderboard(course_id, limit, offset)

    # Get user rank
    user_rank = None
    for i, entry in enumerate(entries):
        if entry["user_id"] == current_user.id:
            user_rank = entry["rank"]
            break

    return LeaderboardResponse(
        leaderboard_type="arena",
        course_id=course_id,
        entries=entries,
        user_rank=user_rank,
    )


# ========== Mastery Quiz Endpoints (精进之路测试) ==========

from app.services.mastery_quiz import mastery_quiz_service
from app.schemas.mastery_quiz import (
    MasteryQuizGenerateRequest,
    MasteryQuizSubmitRequest,
)


@router.get("/mastery/{course_id}/chapter/{chapter_id}/knowledge")
async def get_chapter_knowledge(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节知识点内容（精进之路）

    返回章节的知识点讲解内容，由 AI 生成。
    """
    result = await mastery_quiz_service.get_chapter_knowledge_content(
        db=db, chapter_id=chapter_id, user_id=current_user.id
    )

    if not result:
        raise HTTPException(status_code=404, detail="章节不存在或知识点生成失败")

    return result


@router.post("/mastery/{course_id}/generate-quiz")
async def generate_mastery_quiz(
    course_id: int,
    request: MasteryQuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成精进之路测试题

    根据用户画像和章节知识点，由 AI 生成个性化测试题。
    """
    # 确保请求中的 course_id 与路径一致
    request.course_id = course_id

    result = await mastery_quiz_service.generate_quiz(
        db=db, user_id=current_user.id, request=request
    )

    return result


@router.post("/mastery/{course_id}/submit-quiz")
async def submit_mastery_quiz(
    course_id: int,
    request: MasteryQuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交精进之路测试结果

    评估用户答案，更新学习进度，返回结果和建议。
    """
    result = await mastery_quiz_service.submit_quiz(
        db=db, user_id=current_user.id, request=request
    )

    return result


# ========== Section Base Question Endpoints (精进之路基础测试) ==========

from app.services.section_base_question import section_base_question_service
from app.schemas.section_base_question import (
    BaseAnswersSubmitRequest,
    BaseAnswersSubmitResponse,
    EnhancedQuizGenerateRequest,
    EnhancedQuizGenerateResponse,
    EnhancedQuizSubmitRequest,
    EnhancedQuizSubmitResponse,
    PersistEnhancedQuestionRequest,
    PersistEnhancedQuestionResponse,
)
from app.services.mastery_progress import mastery_progress_service
from app.schemas.mastery_progress import (
    MasteryExerciseProgressSaveRequest,
    MasteryExerciseProgressResponse,
    MasteryChapterProgressResponse,
    MasteryQuizCompleteRequest,
)


@router.get("/mastery/section/{section_id}/knowledge-points")
async def get_section_knowledge_points(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取小节知识点内容（精进之路）

    返回该小节的所有知识点及其学习内容，用户先学习知识点再做测试。
    """
    from app.models.section_knowledge_point import SectionKnowledgePoint

    result = await db.execute(
        select(SectionKnowledgePoint)
        .where(
            SectionKnowledgePoint.section_id == section_id,
            SectionKnowledgePoint.is_active,
        )
        .order_by(SectionKnowledgePoint.order_index)
    )
    knowledge_points = result.scalars().all()

    # 获取小节信息
    section_result = await db.execute(select(Section).where(Section.id == section_id))
    section = section_result.scalar_one_or_none()

    return {
        "section_id": section_id,
        "section_title": section.title if section else "",
        "chapter_id": section.chapter_id if section else None,
        "total_knowledge_points": len(knowledge_points),
        "knowledge_points": [kp.to_dict() for kp in knowledge_points],
    }


@router.get("/mastery/section/{section_id}/base-questions")
async def get_section_base_questions(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取小节基础测试题（精进之路）

    返回该小节的固定基础测试题，用于学习知识点后的基础测试。
    """
    result = await section_base_question_service.get_section_base_questions(
        db=db,
        section_id=section_id,
        user_id=current_user.id,
    )
    return result


@router.post(
    "/mastery/{course_id}/chapter/{chapter_id}/submit-base",
    response_model=BaseAnswersSubmitResponse,
)
async def submit_base_answers(
    course_id: int,
    chapter_id: int,
    request: BaseAnswersSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交基础测试题答案（精进之路）

    评估答案，识别薄弱知识点，返回分析结果。
    同时更新用户的 mastery_xp。
    """
    # 使用请求中的 section_id，如果没有则回退到 chapter_id（兼容旧逻辑）
    section_id = request.section_id if request.section_id else chapter_id
    result = await section_base_question_service.submit_base_answers(
        db=db,
        section_id=section_id,
        request=request,
        user_id=current_user.id,
    )
    return result


@router.post(
    "/mastery/{course_id}/generate-enhanced",
    response_model=EnhancedQuizGenerateResponse,
)
async def generate_enhanced_quiz(
    course_id: int,
    request: EnhancedQuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成强化测试题（精进之路）

    根据基础测试识别的薄弱点，AI 生成个性化强化题目。
    """
    logger.info(
        f"[API] generate_enhanced_quiz 开始: course_id={course_id}, user={current_user.id[:8]}..., chapter={request.chapter_id}, weak_points={request.weak_points}"
    )

    request.course_id = course_id
    result = await section_base_question_service.generate_enhanced_quiz(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    logger.info(
        f"[API] generate_enhanced_quiz 完成: success={result.success}, questions_count={len(result.questions) if result.questions else 0}"
    )

    # 如果生成成功，注册WebSocket会话
    if result.success and result.session_id:
        from app.websockets.exercise import websocket_manager

        websocket_manager.register_session(result.session_id, current_user.id)

    return result


@router.get("/mastery/generation-status/{session_id}")
async def get_generation_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取题目生成会话状态（轮询接口）

    返回当前已生成的所有题目和生成进度。
    """
    from app.services.exercise_generator import ExerciseGeneratorService

    generator = ExerciseGeneratorService(db)
    session = await generator.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 获取已生成的题目
    exercises = await generator.get_all_exercises(session_id)

    return {
        "session_id": session_id,
        "status": session.status,
        "total_count": session.total_count,
        "generated_count": session.generated_count,
        "exercises": exercises,
        "is_completed": session.status == "completed",
    }


@router.get("/mastery/generation/{session_id}/exercises")
async def get_session_exercises(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取会话已生成的所有强化题（增强版）（轮询接口）

    前端可以通过轮询此接口来获取新生成的题目。
    """
    questions = await section_base_question_service.get_session_exercises(
        db, session_id
    )

    return {
        "session_id": session_id,
        "questions": [q.model_dump() for q in questions],
        "total_count": len(questions),
    }


@router.post(
    "/mastery/{course_id}/submit-enhanced", response_model=EnhancedQuizSubmitResponse
)
async def submit_enhanced_quiz(
    course_id: int,
    request: EnhancedQuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交强化测试题答案（精进之路）

    评估答案，更新学习进度，返回最终结果。
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"[API] submit_enhanced_quiz 开始: course_id={course_id}, user={current_user.id[:8]}..., session={request.session_id}, answers={len(request.answers)}"
    )

    result = await section_base_question_service.submit_enhanced_quiz(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    logger.info(
        f"[API] submit_enhanced_quiz 完成: correct={result.correct_answers}/{result.total_questions}"
    )
    return result


@router.post(
    "/mastery/{course_id}/persist-enhanced-question",
    response_model=PersistEnhancedQuestionResponse,
)
async def persist_enhanced_question(
    course_id: int,
    request: PersistEnhancedQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    持久化单道强化题到 SectionBaseQuestion（用户做题提交时调用）

    从 ExerciseGenerationSession 中获取指定索引的题目，
    保存到 SectionBaseQuestion 获得真实数据库ID，用于进度保存和错题本跳转。
    """
    print(
        f"\n[ROUTE_DEBUG] === persist_enhanced_question ENDPOINT entered === "
        f"course_id={course_id} user={current_user.id[:8] if current_user else 'NONE'} "
        f"session={request.session_id[:8] if request.session_id else 'NONE'} "
        f"index={request.question_index}",
        flush=True,
    )
    try:
        result = await section_base_question_service.persist_enhanced_question(
            db=db,
            user_id=current_user.id,
            request=request,
        )
        print(
            f"[ROUTE_DEBUG] === persist_enhanced_question RETURNED success={result.success} "
            f"qid={result.question_id} ===",
            flush=True,
        )
        return result
    except Exception as e:
        import traceback

        print(
            f"\n[ROUTE_DEBUG] !!! Router-level exception: {type(e).__name__}: {e}",
            flush=True,
        )
        traceback.print_exc()
        return PersistEnhancedQuestionResponse(
            success=False,
            question_id=0,
            message=f"路由层异常: {type(e).__name__}: {str(e)}",
        )


# ========== Mastery Progress Endpoints (精进之路进度) ==========


@router.post(
    "/mastery/progress/exercise", response_model=MasteryExerciseProgressResponse
)
async def save_mastery_exercise_progress(
    request: MasteryExerciseProgressSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    保存精进之路做题进度

    当用户完成一道题（交卷）时调用。
    """
    logger.debug(
        "[ROUTE-DEBUG] ========== 收到 /mastery/progress/exercise 请求 =========="
    )
    logger.debug(
        f"[ROUTE-DEBUG] course_id={request.course_id}, chapter_id={request.chapter_id}"
    )
    logger.debug(
        f"[ROUTE-DEBUG] section_id={request.section_id}, question_id={request.question_id}"
    )
    result = await mastery_progress_service.save_exercise_progress(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    logger.debug(
        f"[ROUTE-DEBUG] 返回结果: success={result.success}, bkt_debug={result.bkt_debug}"
    )
    return result


@router.get(
    "/mastery/{course_id}/{chapter_id}/progress",
    response_model=MasteryChapterProgressResponse,
)
async def get_mastery_chapter_progress(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取精进之路章节进度

    返回用户在某个章节的完成情况。
    """
    result = await mastery_progress_service.get_chapter_progress(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )
    return result


@router.get("/mastery/{course_id}/{chapter_id}/progress/detail")
async def get_mastery_chapter_detail_progress(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取精进之路章节详细进度

    返回用户在某个章节的详细完成情况，包含每道题的进度信息。
    """
    result = await mastery_progress_service.get_chapter_detail_progress(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )
    return result


@router.post("/mastery/progress/complete-quiz")
async def complete_mastery_quiz(
    request: MasteryQuizCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    完成章节quiz时更新ChapterMastery

    当用户完成整个章节测试后调用，用于更新章节掌握度。
    """
    success = await mastery_progress_service.complete_chapter_quiz(
        db=db,
        user_id=current_user.id,
        request=request,
    )
    return {"success": success, "message": "章节进度已更新" if success else "更新失败"}


@router.get("/mastery/progress/exercise/{exercise_key}")
async def get_mastery_progress_by_key(
    exercise_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    根据exercise_key获取做题进度（用于错题本跳转定位）

    返回进度信息，包括题目ID、章节ID等。
    """
    progress = await mastery_progress_service.get_progress_by_exercise_key(
        db=db,
        user_id=current_user.id,
        exercise_key=exercise_key,
    )
    if not progress:
        return {"found": False, "message": "未找到进度记录"}

    return {
        "found": True,
        "progress": {
            "course_id": progress.course_id,
            "chapter_id": progress.chapter_id,
            "question_id": progress.question_id,
            "question_index": progress.question_index,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
        },
    }


# ========== Arena Infinite Mode Endpoints ==========


class InfiniteSessionStartRequest(BaseModel):
    """Request to start infinite mode session"""

    difficulty_level: int = Field(default=3, ge=1, le=5)
    initial_count: int = Field(default=3, ge=1, le=50)


class InfiniteProgressResponse(BaseModel):
    """Response for infinite mode progress"""

    session_id: str
    current_index: int
    total_exercises: int
    exercises: list[dict]
    correct_count: int
    completed_count: int
    total_stars_earned: int


class SubmitExerciseRequest(BaseModel):
    """Request to submit exercise answer"""

    exercise_id: int
    code: str
    language: str
    test_results: list[dict]


class SubmitExerciseResponse(BaseModel):
    """Response for exercise submission"""

    is_correct: bool
    test_results: list[dict]
    stars_earned: int
    next_unlocked: bool
    added_to_wrong_book: bool
    tier_changed: bool
    new_tier: str | None
    new_sub_tier: int | None
    new_stars: int
    promoted: bool
    demoted: bool
    first_time_correct: bool
    first_time_wrong: bool


class SaveCodeRequest(BaseModel):
    """Request to save code"""

    exercise_id: int
    code: str
    language: str


class SwitchExerciseRequest(BaseModel):
    """Request to switch to a different exercise"""

    target_index: int


class AppendExercisesRequest(BaseModel):
    """Request to append more exercises"""

    count: int = Field(default=5, ge=1, le=20)
    difficulty_level: Optional[int] = Field(
        default=None, ge=1, le=8, description="难度等级，不传则从用户现有题目推断"
    )


class ExitSaveRequest(BaseModel):
    """Request to save on exit"""

    current_exercise_id: int
    current_code: str
    current_language: str


# ========================================
# Challenge Path APIs (No Session Concept)
# ========================================


@router.post("/challenge/infinite/start", response_model=ChallengeSessionResponse)
async def start_infinite_session(
    request: InfiniteSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start or get challenge path (independent of courses)"""
    service = ChallengeSelectionService(db)

    try:
        exercises, is_new = await service.get_or_create_challenge_path(
            user_id=current_user.id,
            difficulty_level=request.difficulty_level,
            initial_count=request.initial_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    exercise_list = [map_exercise_summary(ex, i) for i, ex in enumerate(exercises)]

    # Use a fixed session_id for global challenge path
    pseudo_session_id = "challenge-global"

    return ChallengeSessionResponse(
        session_id=pseudo_session_id,
        difficulty_level=request.difficulty_level,
        exercises=exercise_list,
        time_limit=0,
        score_multiplier=1.0,
        status="in_progress",
    )


@router.get("/challenge/progress")
async def get_challenge_path_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lite: bool = Query(
        True, description="Lite mode: skip full content/test_cases for faster loading"
    ),
):
    """Get challenge path progress (independent of courses)

    lite=True (default): Returns metadata only (title, difficulty, progress state).
    Lite mode dramatically reduces response size for users with many exercises.
    Use lite=False to get full content including test_cases.
    """
    service = ChallengeProgressService(db)

    progress = await service.get_progress(
        user_id=current_user.id,
        lite=lite,
    )

    return progress


@router.post("/challenge/submit")
async def submit_challenge_exercise(
    request: SubmitExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit exercise answer in challenge path"""
    service = ChallengeSubmissionService(db)

    try:
        result = await service.submit_exercise(
            user_id=current_user.id,
            exercise_id=request.exercise_id,
            code=request.code,
            language=request.language,
            test_results=request.test_results,
        )
    except (
        ChallengeExerciseNotFoundError,
        ChallengeProgressNotFoundError,
        MissingChallengeTestCasesError,
        UnsupportedChallengeLanguageError,
    ) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except JudgeUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail="Judge service unavailable",
        ) from error

    return result


@router.post("/challenge/save-code")
async def save_challenge_code(
    request: SaveCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save code for an exercise"""
    service = ChallengeProgressService(db)

    success = await service.save_code(
        user_id=current_user.id,
        exercise_id=request.exercise_id,
        code=request.code,
        language=request.language,
    )

    return {"success": success}


@router.post("/challenge/switch")
async def switch_challenge_exercise(
    request: SwitchExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch to a different exercise by index"""
    service = ChallengeProgressService(db)

    try:
        result = await service.switch_exercise(
            user_id=current_user.id,
            target_index=request.target_index,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return map_switch_response(result)


@router.post("/challenge/append")
async def append_challenge_exercises(
    request: AppendExercisesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Append more exercises to challenge path"""
    service = ChallengeSelectionService(db)

    try:
        new_ids = await service.append_exercises(
            user_id=current_user.id,
            difficulty_level=request.difficulty_level,
            count=request.count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"new_exercise_ids": new_ids, "count": len(new_ids)}


@router.post("/challenge/exit")
async def exit_challenge_path(
    request: ExitSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save progress and exit challenge path"""
    service = ChallengeProgressService(db)

    success = await service.save_code(
        user_id=current_user.id,
        exercise_id=request.current_exercise_id,
        code=request.current_code,
        language=request.current_language,
    )

    return {"success": success, "message": "Progress saved"}


@router.get("/challenge/exercise/{exercise_id:int}")
async def get_challenge_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific exercise info - returns full content for on-demand loading (lite mode)"""
    service = ChallengeProgressService(db)

    result = await service.get_exercise_by_id(
        user_id=current_user.id,
        exercise_id=exercise_id,
    )

    if not result:
        raise HTTPException(
            status_code=404, detail="Exercise not found in challenge path"
        )

    total = await service._get_exercise_count(current_user.id)

    return map_exercise_detail_response(result, total_exercises=total)


class RecentArenaExercise(BaseModel):
    """最近挑战之路练习"""

    exercise_id: int
    title: str
    is_correct: bool
    difficulty: int


@router.get("/challenge/recent", response_model=list[RecentArenaExercise])
async def get_recent_arena_exercises(
    limit: int = Query(default=3, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取挑战之路最近练习的题目（含正确情况）- 全局，不关联课程"""
    service = ChallengeProgressService(db)
    recent = await service.get_recent_exercises(user_id=current_user.id, limit=limit)
    return [RecentArenaExercise(**item) for item in recent]


# ========== BKT Mastery Endpoints (小节/章节/课程 三层聚合) ==========


class SectionMasteryResponse(BaseModel):
    """小节掌握度响应"""

    section_id: int
    chapter_id: int
    mastery_score: float
    bkt_aggregated_p_l: float
    knowledge_points_count: int
    mastered_points_count: int
    is_completed: bool
    knowledge_points: list[dict]


class CourseMasteryResponse(BaseModel):
    """课程掌握度响应"""

    course_id: int
    course_name: str  # 课程名称
    mastery_score: float
    progress_percentage: float
    chapters_count: int
    completed_chapters: int
    is_completed: bool
    chapters: list[dict]


@router.get("/mastery/section/{section_id}", response_model=SectionMasteryResponse)
async def get_section_mastery(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取小节掌握度（BKT 聚合）"""
    from app.models.section import Section
    from app.models.section_mastery import SectionMastery
    from app.models.knowledge_point_mastery import KnowledgePointMastery

    # 获取小节信息
    section_result = await db.execute(select(Section).where(Section.id == section_id))
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # 获取小节掌握度
    mastery_result = await db.execute(
        select(SectionMastery).where(
            SectionMastery.user_id == current_user.id,
            SectionMastery.section_id == section_id,
        )
    )
    section_mastery = mastery_result.scalar_one_or_none()

    # 获取章节内所有知识点掌握状态
    kp_result = await db.execute(
        select(KnowledgePointMastery).where(
            KnowledgePointMastery.user_id == current_user.id,
            KnowledgePointMastery.chapter_id == section.chapter_id,
        )
    )
    kp_masteries = kp_result.scalars().all()

    knowledge_points = []
    for kp in kp_masteries:
        knowledge_points.append(
            {
                "name": kp.knowledge_point,
                "p_l": kp.p_l,
                "is_mastered": kp.p_l >= 0.95,
                "total_attempts": kp.total_attempts,
                "correct_attempts": kp.correct_attempts,
            }
        )

    if section_mastery:
        return SectionMasteryResponse(
            section_id=section_id,
            chapter_id=section.chapter_id,
            mastery_score=section_mastery.mastery_score,
            bkt_aggregated_p_l=section_mastery.bkt_aggregated_p_l,
            knowledge_points_count=section_mastery.knowledge_points_count,
            mastered_points_count=section_mastery.mastered_points_count,
            is_completed=section_mastery.is_completed,
            knowledge_points=knowledge_points,
        )
    else:
        # 返回默认值
        return SectionMasteryResponse(
            section_id=section_id,
            chapter_id=section.chapter_id,
            mastery_score=15.0,
            bkt_aggregated_p_l=0.15,
            knowledge_points_count=0,
            mastered_points_count=0,
            is_completed=False,
            knowledge_points=knowledge_points,
        )


@router.get("/mastery/course/{course_id}", response_model=CourseMasteryResponse)
async def get_course_mastery(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取课程掌握度（BKT 四层聚合顶层）"""
    from app.services.bkt_mastery import BKTMasteryService

    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"[API] get_course_mastery: course_id={course_id}, user={current_user.id[:8]}..."
    )

    # 获取课程名称
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    course_name = course.name if course else f"课程 {course_id}"

    bkt_service = BKTMasteryService(db)
    summary = await getattr(bkt_service, "get_course_mastery_summary")(
        current_user.id, course_id
    )

    logger.info(
        f"[API] get_course_mastery result: chapters_count={summary['chapters_count']}, chapters={len(summary.get('chapters', []))}"
    )

    return CourseMasteryResponse(
        course_id=course_id,
        course_name=course_name,
        mastery_score=summary["mastery_score"],
        progress_percentage=summary["progress_percentage"],
        chapters_count=summary["chapters_count"],
        completed_chapters=summary["completed_chapters"],
        is_completed=summary["is_completed"],
        chapters=summary["chapters"],
    )
