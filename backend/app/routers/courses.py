"""Course API Router"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.section_progress import SectionProgress
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.course import (
    CourseListResponse,
    CourseDetailResponse,
    CourseSummary,
    ChapterSummary,
    ChapterDetail,
    ExerciseSummary,
    ChapterDetailResponse,
    CourseDetail,
)
from app.schemas.section import (
    SectionSummary,
    SectionDetail,
    SectionListResponse,
    SectionDetailResponse,
    SaveSectionProgressRequest,
    SectionProgressResponse,
    CurrentPositionResponse,
)
from app.utils.time import utc_now

router = APIRouter(prefix="/api/courses", tags=["courses"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]

# Import dependencies directly from deps module
from app.utils.deps import get_current_active_user, get_optional_user

auth_dependency = Annotated[User, Depends(get_current_active_user)]
optional_user_dependency = Annotated[Optional[User], Depends(get_optional_user)]


# 8门课程初始化数据
COURSES_INIT_DATA = [
    {"code": "C", "name": "C语言程序设计", "difficulty_level": 1, "icon": "c"},
    {"code": "CPP", "name": "C++程序设计", "difficulty_level": 2, "icon": "cpp"},
    {"code": "Python", "name": "Python程序设计", "difficulty_level": 1, "icon": "python"},
    {"code": "Java", "name": "Java程序设计", "difficulty_level": 2, "icon": "java"},
    {"code": "Rust", "name": "Rust程序设计", "difficulty_level": 4, "icon": "rust"},
    {"code": "DSA", "name": "数据结构与算法", "difficulty_level": 3, "icon": "dsa"},
    {"code": "ADA", "name": "算法设计与分析", "difficulty_level": 4, "icon": "ada"},
    {"code": "DiscreteMath", "name": "离散数学", "difficulty_level": 3, "icon": "math"},
]


@router.get("", response_model=CourseListResponse)
async def get_courses(db: db_dependency):
    """
    Get all active courses with chapter count.

    Returns a list of courses with basic info and chapter count.
    This endpoint is public - no authentication required.
    """
    query = (
        select(
            Course,
            func.count(Chapter.id).label("chapter_count")
        )
        .outerjoin(Chapter, Course.id == Chapter.course_id)
        .where(Course.is_active == True)
        .group_by(Course.id)
        .order_by(Course.difficulty_level, Course.code)
    )

    result = await db.execute(query)
    rows = result.all()

    courses = []
    for course, chapter_count in rows:
        courses.append(CourseSummary(
            id=course.id,
            code=course.code,
            name=course.name,
            description=course.description,
            difficulty_level=course.difficulty_level,
            icon=course.icon,
            is_active=course.is_active,
            chapter_count=chapter_count
        ))

    return CourseListResponse(courses=courses, total=len(courses))


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    db: db_dependency,
    user: optional_user_dependency = None
):
    """
    Get course details including chapters.

    Returns course info with embedded chapter list.
    If authenticated, also returns enrolled status.
    """
    query = (
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.chapters))
    )

    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )

    chapters = [
        ChapterSummary.model_validate(ch)
        for ch in sorted(course.chapters, key=lambda x: x.order_index)
        if ch.is_active
    ]

    course_detail = CourseDetail.model_validate(course)
    course_detail.chapters = chapters

    # Check if user is enrolled (if authenticated)
    enrolled = False
    if user:
        enrolled_ids = user.courses_enrolled or []
        enrolled = course_id in enrolled_ids

    return CourseDetailResponse(course=course_detail, enrolled=enrolled)


@router.get("/code/{code}", response_model=CourseDetailResponse)
async def get_course_by_code(code: str, db: db_dependency):
    """
    Get course details by course code.

    Returns course info with embedded chapter list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Course)
        .where(Course.code == code)
        .options(selectinload(Course.chapters))
    )

    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code '{code}' not found"
        )

    chapters = [
        ChapterSummary.model_validate(ch)
        for ch in sorted(course.chapters, key=lambda x: x.order_index)
        if ch.is_active
    ]

    course_detail = CourseDetail.model_validate(course)
    course_detail.chapters = chapters

    return CourseDetailResponse(course=course_detail)


# Direct chapter access by chapter ID (for frontend convenience)
@router.get("/chapters/{chapter_id}", response_model=ChapterDetailResponse)
async def get_chapter_by_id(chapter_id: int, db: db_dependency):
    """
    Get chapter details by chapter ID directly.

    Returns chapter info with embedded exercise list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Chapter)
        .where(Chapter.id == chapter_id)
        .options(selectinload(Chapter.exercises))
    )

    result = await db.execute(query)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    exercises = [
        ExerciseSummary(
            id=ex.id,
            chapter_id=ex.chapter_id,
            source=ex.source,
            source_id=ex.source_id,
            type=ex.type,
            difficulty=ex.difficulty,
            content=ex.content,
            hints=ex.hints,
        )
        for ex in chapter.exercises
    ]

    chapter_detail = ChapterDetail(
        id=chapter.id,
        course_id=chapter.course_id,
        title=chapter.title,
        description=chapter.description,
        content=chapter.content,
        order_index=chapter.order_index,
        learning_objectives=chapter.learning_objectives,
        difficulty_tags=chapter.difficulty_tags,
        skill_tags=chapter.skill_tags,
        estimated_minutes=chapter.estimated_minutes,
        is_active=chapter.is_active,
    )

    return ChapterDetailResponse(chapter=chapter_detail, exercises=exercises)


@router.get("/{course_id}/chapters/{chapter_id}", response_model=ChapterDetailResponse)
async def get_chapter(course_id: int, chapter_id: int, db: db_dependency):
    """
    Get chapter details including exercises.

    Returns chapter info with embedded exercise list.
    This endpoint is public - no authentication required.
    """
    query = (
        select(Chapter)
        .where(Chapter.id == chapter_id, Chapter.course_id == course_id)
        .options(selectinload(Chapter.exercises))
    )

    result = await db.execute(query)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found in course {course_id}"
        )

    exercises = [
        ExerciseSummary(
            id=ex.id,
            chapter_id=ex.chapter_id,
            source=ex.source,
            source_id=ex.source_id,
            type=ex.type,
            difficulty=ex.difficulty,
            content=ex.content,
            hints=ex.hints,
        )
        for ex in chapter.exercises
    ]

    chapter_detail = ChapterDetail(
        id=chapter.id,
        course_id=chapter.course_id,
        title=chapter.title,
        description=chapter.description,
        content=chapter.content,
        order_index=chapter.order_index,
        learning_objectives=chapter.learning_objectives,
        difficulty_tags=chapter.difficulty_tags,
        skill_tags=chapter.skill_tags,
        estimated_minutes=chapter.estimated_minutes,
        is_active=chapter.is_active,
    )

    return ChapterDetailResponse(chapter=chapter_detail, exercises=exercises)


@router.post("/{course_id}/enroll")
async def enroll_course(
    course_id: int,
    db: db_dependency,
    current_user: User = Depends(get_current_active_user)
):
    """
    Enroll current user in a course.

    Adds the course to user's enrolled courses list.
    """
    try:
        # Check course exists
        result = await db.execute(
            select(Course).where(Course.id == course_id, Course.is_active == True)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found"
            )

        # Re-fetch user in current session to ensure it's attached
        user_result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if already enrolled - handle None case
        enrolled = list(user.courses_enrolled) if user.courses_enrolled else []
        if course_id in enrolled:
            return {
                "message": f"Already enrolled in {course.name}",
                "course_id": course_id,
                "enrolled_courses": enrolled,
                "already_enrolled": True
            }

        # Add to enrolled courses - create new list to trigger SQLAlchemy change detection
        enrolled.append(course_id)
        user.courses_enrolled = enrolled  # Assign new list to trigger change

        # Mark the attribute as modified for SQLAlchemy (needed for JSON fields)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "courses_enrolled")

        await db.commit()

        return {
            "message": f"Successfully enrolled in {course.name}",
            "course_id": course_id,
            "enrolled_courses": enrolled
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrollment failed: {str(e)}"
        )


@router.get("/users/me/course-progress")
async def get_user_course_progress(
    db: db_dependency,
    current_user: auth_dependency
):
    """
    Get progress for all courses for the current user.

    Returns a list of all 8 courses with user's progress in each:
    - Progress percentage (based on chapter mastery)
    - Mastery score (for 精进之路)
    - Arena tier and score (for 挑战之路)
    - Current chapter
    - Current section (within current chapter)
    """
    from app.models.chapter_mastery import ChapterMastery
    from app.models.user_arena import UserArenaProfile

    # Get all courses
    courses_result = await db.execute(
        select(Course).where(Course.is_active == True).order_by(Course.difficulty_level, Course.code)
    )
    all_courses = courses_result.scalars().all()

    # Get total chapters per course
    total_chapters_result = await db.execute(
        select(Chapter.course_id, func.count(Chapter.id).label('count'))
        .where(Chapter.is_active == True)
        .group_by(Chapter.course_id)
    )
    total_chapters_map = {row.course_id: row.count for row in total_chapters_result.all()}

    # Get user's mastery scores per course
    mastery_result = await db.execute(
        select(ChapterMastery.course_id, func.sum(ChapterMastery.mastery_score).label('total_mastery'), func.count(ChapterMastery.id).label('chapter_count'))
        .where(ChapterMastery.user_id == current_user.id)
        .group_by(ChapterMastery.course_id)
    )
    mastery_map = {row.course_id: {"total": row.total_mastery, "chapters": row.chapter_count} for row in mastery_result.all()}

    # Get user's arena profiles per course
    arena_result = await db.execute(
        select(UserArenaProfile).where(UserArenaProfile.user_id == current_user.id)
    )
    arena_profiles = {p.course_id: p for p in arena_result.scalars().all()}

    # Get current chapter per course (first chapter with mastery < 75)
    current_chapter_result = await db.execute(
        select(ChapterMastery.chapter_id, ChapterMastery.course_id, ChapterMastery.mastery_score, Chapter.title)
        .join(Chapter, ChapterMastery.chapter_id == Chapter.id)
        .where(ChapterMastery.user_id == current_user.id, ChapterMastery.mastery_score < 75)
        .order_by(ChapterMastery.course_id, Chapter.order_index)
    )
    current_chapter_map = {}
    current_chapter_id_map = {}
    for row in current_chapter_result.all():
        if row.course_id not in current_chapter_map:
            current_chapter_map[row.course_id] = row.title
            current_chapter_id_map[row.course_id] = row.chapter_id

    # Get current section per course (first section of current chapter, or based on progress)
    current_section_map = {}
    for course_id, chapter_id in current_chapter_id_map.items():
        # Get first section of the current chapter (simplified approach)
        section_result = await db.execute(
            select(Section)
            .where(Section.chapter_id == chapter_id, Section.is_active == True)
            .order_by(Section.order_index)
            .limit(1)
        )
        first_section = section_result.scalar_one_or_none()
        if first_section:
            current_section_map[course_id] = first_section.title

    # Build response
    courses_data = []
    for course in all_courses:
        total_chapters = total_chapters_map.get(course.id, 0)
        mastery_data = mastery_map.get(course.id, {"total": 0, "chapters": 0})

        # Calculate progress based on mastered chapters (mastery >= 75)
        mastered_chapters = mastery_data["chapters"] if mastery_data["total"] else 0
        progress = round((mastered_chapters / total_chapters) * 100, 1) if total_chapters > 0 else 0

        # Get mastery and arena data
        mastery_score = round(mastery_data["total"], 2) if mastery_data["total"] else None
        arena_profile = arena_profiles.get(course.id)

        courses_data.append({
            "course_id": course.id,
            "course_code": course.code,
            "course_name": course.name,
            "progress": progress,
            "completed_stages": mastered_chapters,
            "total_stages": total_chapters,
            "current_chapter": current_chapter_map.get(course.id),
            "current_section": current_section_map.get(course.id),
            "mastery_score": mastery_score,
            "arena_tier": arena_profile.tier if arena_profile else None,
            "arena_sub_tier": arena_profile.sub_tier if arena_profile else None,
            "arena_stars": arena_profile.stars if arena_profile else None,
        })

    return {"courses": courses_data}


@router.post("/init")
async def init_courses(db: db_dependency, user: auth_dependency):
    """
    Initialize the 8 courses if they don't exist.

    Admin only endpoint.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    created = []
    for course_data in COURSES_INIT_DATA:
        # Check if exists
        result = await db.execute(
            select(Course).where(Course.code == course_data["code"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            course = Course(
                code=course_data["code"],
                name=course_data["name"],
                difficulty_level=course_data["difficulty_level"],
                icon=course_data["icon"],
                is_active=True
            )
            db.add(course)
            created.append(course_data["code"])

    await db.flush()

    return {
        "message": f"Created {len(created)} new courses",
        "created": created
    }


# ========== Section Endpoints ==========

@router.get("/chapters/{chapter_id}/sections", response_model=SectionListResponse)
async def get_chapter_sections(
    chapter_id: int,
    db: db_dependency,
    current_user: auth_dependency
):
    """
    Get all sections for a chapter with user's completion status and BKT mastery.
    """
    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Get all sections for this chapter
    sections_result = await db.execute(
        select(Section)
        .where(Section.chapter_id == chapter_id, Section.is_active == True)
        .order_by(Section.order_index)
    )
    sections = sections_result.scalars().all()

    # Get user's progress for these sections
    section_ids = [s.id for s in sections]
    progress_result = await db.execute(
        select(SectionProgress).where(
            SectionProgress.user_id == current_user.id,
            SectionProgress.section_id.in_(section_ids)
        )
    )
    progress_map = {p.section_id: p for p in progress_result.scalars().all()}

    # Get BKT mastery for these sections
    from app.models.section_mastery import SectionMastery
    mastery_result = await db.execute(
        select(SectionMastery).where(
            SectionMastery.user_id == current_user.id,
            SectionMastery.section_id.in_(section_ids)
        )
    )
    mastery_map = {m.section_id: m for m in mastery_result.scalars().all()}

    # Build response
    section_summaries = []
    for section in sections:
        progress = progress_map.get(section.id)
        mastery = mastery_map.get(section.id)
        section_summaries.append(SectionSummary(
            id=section.id,
            chapter_id=section.chapter_id,
            title=section.title,
            description=section.description,
            order_index=section.order_index,
            estimated_minutes=section.estimated_minutes,
            is_completed=progress.is_completed if progress else False,
            mastery_score=mastery.mastery_score if mastery else None,
        ))

    return SectionListResponse(sections=section_summaries, total=len(section_summaries))


@router.get("/sections/{section_id}", response_model=SectionDetailResponse)
async def get_section(
    section_id: int,
    db: db_dependency,
    current_user: auth_dependency
):
    """
    Get section details including content.
    """
    # Get section
    result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section {section_id} not found"
        )

    # Get user's progress
    progress_result = await db.execute(
        select(SectionProgress).where(
            SectionProgress.user_id == current_user.id,
            SectionProgress.section_id == section_id
        )
    )
    progress = progress_result.scalar_one_or_none()

    section_detail = SectionDetail(
        id=section.id,
        chapter_id=section.chapter_id,
        title=section.title,
        description=section.description,
        content=section.content,
        order_index=section.order_index,
        estimated_minutes=section.estimated_minutes,
        learning_objectives=section.learning_objectives,
        is_completed=progress.is_completed if progress else False,
        last_position=progress.last_position if progress else "content",
    )

    return SectionDetailResponse(section=section_detail)


@router.post("/sections/{section_id}/progress", response_model=SectionProgressResponse)
async def save_section_progress(
    section_id: int,
    request: SaveSectionProgressRequest,
    db: db_dependency,
    current_user: auth_dependency
):
    """
    Save user's learning progress for a section.
    """
    # Verify section exists
    section_result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section {section_id} not found"
        )

    # Get or create progress record
    progress_result = await db.execute(
        select(SectionProgress).where(
            SectionProgress.user_id == current_user.id,
            SectionProgress.section_id == section_id
        )
    )
    progress = progress_result.scalar_one_or_none()

    if not progress:
        progress = SectionProgress(
            user_id=current_user.id,
            section_id=section_id,
            last_position=request.position,
            is_completed=request.is_completed,
        )
        if request.is_completed:
            progress.completed_at = utc_now()
        db.add(progress)
    else:
        progress.last_position = request.position
        if request.is_completed and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = utc_now()

    await db.commit()
    await db.refresh(progress)

    return SectionProgressResponse(
        section_id=progress.section_id,
        is_completed=progress.is_completed,
        last_position=progress.last_position,
        completed_at=progress.completed_at,
    )


@router.get("/{course_id}/current-position", response_model=CurrentPositionResponse)
async def get_current_position(
    course_id: int,
    db: db_dependency,
    current_user: auth_dependency
):
    """
    Get user's current learning position for a course.
    Returns the first incomplete section, or the last completed section.
    """

    # Get all chapters for this course
    chapters_result = await db.execute(
        select(Chapter)
        .where(Chapter.course_id == course_id, Chapter.is_active == True)
        .order_by(Chapter.order_index)
    )
    chapters = chapters_result.scalars().all()

    if not chapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chapters found for course {course_id}"
        )

    # Get all sections for these chapters
    chapter_ids = [c.id for c in chapters]
    sections_result = await db.execute(
        select(Section)
        .where(Section.chapter_id.in_(chapter_ids), Section.is_active == True)
        .order_by(Section.chapter_id, Section.order_index)
    )
    sections = sections_result.scalars().all()

    if not sections:
        # No sections, return first chapter
        return CurrentPositionResponse(
            course_id=course_id,
            chapter_id=chapters[0].id,
            section_id=0,
            position="content",
            chapter_title=chapters[0].title,
            section_title=None,
        )

    # Get user's progress for all sections
    section_ids = [s.id for s in sections]
    progress_result = await db.execute(
        select(SectionProgress).where(
            SectionProgress.user_id == current_user.id,
            SectionProgress.section_id.in_(section_ids)
        )
    )
    progress_map = {p.section_id: p for p in progress_result.scalars().all()}

    # Find first incomplete section
    for section in sections:
        progress = progress_map.get(section.id)
        if not progress or not progress.is_completed:
            # Found incomplete section
            chapter = next((c for c in chapters if c.id == section.chapter_id), None)
            return CurrentPositionResponse(
                course_id=course_id,
                chapter_id=section.chapter_id,
                section_id=section.id,
                position=progress.last_position if progress else "content",
                chapter_title=chapter.title if chapter else None,
                section_title=section.title,
            )

    # All sections completed, return last section
    last_section = sections[-1]
    last_chapter = next((c for c in chapters if c.id == last_section.chapter_id), None)
    last_progress = progress_map.get(last_section.id)

    return CurrentPositionResponse(
        course_id=course_id,
        chapter_id=last_section.chapter_id,
        section_id=last_section.id,
        position=last_progress.last_position if last_progress else "content",
        chapter_title=last_chapter.title if last_chapter else None,
        section_title=last_section.title,
    )


# ========================================
# Hybrid Recommendation API
# ========================================

from app.services.hybrid_recommendation import HybridRecommendationService
from app.services.user_profile import UserProfileService
from app.services.embedding import get_embedding_service, get_exercise_embedding_service
from app.services.tag_extraction import get_tag_extraction_service
from app.models.user_arena import UserArenaProfile
from app.models.chapter_mastery import ChapterMastery


class HybridRecommendationRequest:
    """Request model for hybrid recommendation"""
    course_id: int
    limit: int = 10
    min_difficulty: int = 1
    max_difficulty: int = 8


class EmbeddingConfigRequest:
    """Request model for updating embedding configuration"""
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@router.get("/{course_id}/hybrid-recommendations")
async def get_hybrid_recommendations(
    course_id: int,
    db: db_dependency,
    current_user: auth_dependency,
    limit: int = 10,
    min_difficulty: int = 1,
    max_difficulty: int = 8,
):
    """
    Get personalized exercise recommendations using hybrid algorithm.

    Combines:
    - 40% Behavior-based scoring
    - 35% Embedding similarity
    - 25% Difficulty matching (ZPD)
    """
    service = HybridRecommendationService(db)
    recommendations = await service.get_recommendations(
        user_id=current_user.id,
        course_id=course_id,
        limit=limit,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty,
    )

    return {
        "course_id": course_id,
        "recommendations": recommendations,
        "algorithm": {
            "name": "Hybrid Recommendation",
            "weights": {
                "behavior": 0.40,
                "embedding": 0.35,
                "difficulty": 0.25,
            },
        },
    }


@router.get("/{course_id}/user-profile")
async def get_user_profile_stats(
    course_id: int,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get user profile statistics for hybrid recommendation.
    """
    service = UserProfileService(db)
    stats = await service.get_user_stats(current_user.id, course_id)

    return {
        "course_id": course_id,
        "user_stats": stats,
    }


@router.post("/{course_id}/recalculate-profile")
async def recalculate_user_profile(
    course_id: int,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Recalculate user profile embedding from all exercise history.
    """
    service = UserProfileService(db)
    result = await service.recalculate_full_embedding(current_user.id, course_id)

    return {
        "course_id": course_id,
        "result": result,
    }


@router.post("/exercises/{exercise_id}/extract-tags")
async def extract_exercise_tags(
    exercise_id: int,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Extract structured tags from an exercise using AI.
    """
    # Get exercise
    result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise {exercise_id} not found"
        )

    # Extract tags
    service = get_tag_extraction_service()
    content = exercise.content or {}
    tags = await service.extract_tags(
        question_text=content.get("text", "") or content.get("description", ""),
        exercise_type=exercise.type,
        options=content.get("options"),
        code_template=content.get("code_template"),
        existing_knowledge_points=exercise.knowledge_points,
    )

    # Save to exercise
    exercise.extracted_tags = tags.to_dict()
    await db.commit()

    return {
        "exercise_id": exercise_id,
        "extracted_tags": tags.to_dict(),
        "embedding_text": tags.to_embedding_text(),
    }


@router.post("/exercises/{exercise_id}/generate-embedding")
async def generate_exercise_embedding(
    exercise_id: int,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Generate embedding for an exercise.
    """
    service = get_exercise_embedding_service(db)
    embedding = await service.generate_and_store_embedding(exercise_id)

    if embedding is None:
        return {
            "exercise_id": exercise_id,
            "success": False,
            "message": "Failed to generate embedding. Check AI API configuration.",
        }

    return {
        "exercise_id": exercise_id,
        "success": True,
        "embedding_dimensions": len(embedding),
    }


@router.post("/batch-update-embeddings")
async def batch_update_embeddings(
    db: db_dependency,
    current_user: auth_dependency,
    limit: int = 50,
):
    """
    Batch update embeddings for exercises without embeddings.
    """
    service = get_exercise_embedding_service(db)
    result = await service.batch_update_embeddings(limit=limit)

    return {
        "result": result,
    }


@router.get("/recommendation-debug/{course_id}")
async def debug_recommendation_system(
    course_id: int,
    db: db_dependency,
    current_user: auth_dependency,
    min_difficulty: int = 1,
    max_difficulty: int = 8,
):
    """
    Debug endpoint to see all components of the hybrid recommendation system.
    """
    # Get user stats
    profile_service = UserProfileService(db)
    user_stats = await profile_service.get_user_stats(current_user.id, course_id)

    # Get recommendations
    hybrid_service = HybridRecommendationService(db)
    recommendations = await hybrid_service.get_recommendations(
        user_id=current_user.id,
        course_id=course_id,
        limit=5,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty,
    )

    # Get exercises with embeddings count
    exercises_with_embedding = await db.execute(
        select(func.count()).select_from(Exercise).where(
            Exercise.is_verified == True,
            Exercise.embedding.isnot(None),
        )
    )
    total_with_embedding = exercises_with_embedding.scalar() or 0

    # Get total exercises
    total_exercises = await db.execute(
        select(func.count()).select_from(Exercise).where(Exercise.is_verified == True)
    )
    total = total_exercises.scalar() or 0

    # Check embedding service configuration
    from app.config import get_settings
    settings = get_settings()
    embedding_configured = bool(settings.EMBEDDING_API_KEY)

    return {
        "course_id": course_id,
        "user_stats": user_stats,
        "recommendations": recommendations,
        "system_status": {
            "total_exercises": total,
            "exercises_with_embedding": total_with_embedding,
            "embedding_coverage": f"{(total_with_embedding / total * 100):.1f}%" if total > 0 else "N/A",
            "embedding_service_configured": embedding_configured,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL,
        },
        "fusion_weights": hybrid_service.get_fusion_weights(),
    }
