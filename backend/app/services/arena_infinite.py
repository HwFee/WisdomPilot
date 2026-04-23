"""
Challenge Path Service (挑战之路服务)

Service for managing Challenge Path:
- No session concept - direct course-based management
- Persistent exercise records per user per course
- New exercises are appended to existing list
- exercise_id is stable for wrong question book / favorites integration

Design:
- Each course has ONE challenge path per user
- Old exercises have fixed index, new exercises are appended
- exercise_id is used for cross-references (wrong book, favorites, notes)
- Uses AdaptiveRecommendationService for intelligent exercise matching based on user profile
"""

import logging
import random
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog
from app.models.user import User
from app.models.user_arena import UserArenaProfile
from app.services.adaptive_recommendation import (
    AdaptiveRecommendationService,
)
from app.services.hybrid_recommendation import HybridRecommendationService
from app.services.user_profile import UserProfileService
from app.services.wrong_question import wrong_question_service
from app.services.tier_service import tier_service
from app.services.core_service import CoreService
from app.core.tier_config import TierRank, tier_from_string

# 创建日志器
logger = logging.getLogger(__name__)

# Core rewards for challenge path
CORE_REWARD_CHALLENGE_CORRECT = 3  # Cores earned for correct answer in challenge path


class ChallengePathService:
    """Service for Challenge Path operations - no session concept"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _is_strict_passed(value: object) -> bool:
        """Accept only explicit pass-like values.

        This avoids Python truthiness pitfalls like bool("false") == True.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "pass", "passed", "ok"}
        return False

    @classmethod
    def _all_test_cases_passed(cls, test_results: list[dict]) -> bool:
        """Return True only when every test case is explicitly passed."""
        if not test_results:
            return False

        return all(cls._is_strict_passed(result.get("passed")) for result in test_results)

    # ========================================
    # Core Methods - Course-based Management
    # ========================================

    async def get_or_create_challenge_path(
        self,
        user_id: str,
        
        difficulty_level: int = 3,
        initial_count: int = 5,
    ) -> tuple[list[Exercise], bool]:
        """Get existing exercises or create initial set

        Returns:
            tuple: (exercises, is_new)
        """
        # Get existing progress records
        existing_progress = await self._get_user_progress(user_id)

        if existing_progress:
            # User has existing exercises - fetch them
            exercises = await self._get_exercises_from_progress(existing_progress)
            return exercises, False

        # No existing exercises - create initial set
        exercises = await self._create_initial_exercises(
            user_id, difficulty_level, initial_count
        )
        return exercises, True

    async def _get_user_progress(
        self,
        user_id: str,
        
    ) -> list[ArenaExerciseProgress]:
        """Get all progress records for user's challenge path in a course"""
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                
            )
            .order_by(ArenaExerciseProgress.exercise_index)
        )
        return list(result.scalars().all())

    async def _get_exercises_from_progress(
        self,
        progress_records: list[ArenaExerciseProgress],
    ) -> list[Exercise]:
        """Fetch Exercise objects from progress records"""
        exercise_ids = [p.exercise_id for p in progress_records]
        if not exercise_ids:
            return []

        result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises_map = {ex.id: ex for ex in result.scalars().all()}

        # Return in order of exercise_index
        return [
            exercises_map[p.exercise_id]
            for p in progress_records
            if p.exercise_id in exercises_map
        ]

    async def _create_initial_exercises(
        self,
        user_id: str,
        
        difficulty_level: int,
        count: int,
    ) -> list[Exercise]:
        """Create initial exercise set for a new challenge path using hybrid recommendation"""
        # Get user for adaptive recommendation
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if user:
            # Try hybrid recommendation first (if user has behavior data)
            hybrid_service = HybridRecommendationService(self.db)
            recommendations = await hybrid_service.get_recommendations(
                user_id=user_id,
                course_id=None,
                limit=count,
                min_difficulty=max(1, difficulty_level - 1),
                max_difficulty=min(8, difficulty_level + 1),
            )

            if recommendations:
                recommended_ids = [rec["exercise_id"] for rec in recommendations]

                # Fetch recommended exercises
                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                # Preserve recommendation order
                selected = [
                    exercises_map[eid]
                    for eid in recommended_ids
                    if eid in exercises_map
                ]

                if len(selected) >= count:
                    # Create progress records
                    for i, ex in enumerate(selected[:count]):
                        progress = ArenaExerciseProgress(
                            user_id=user_id,
                            
                            exercise_id=ex.id,
                            exercise_index=i,
                            is_unlocked=(i == 0),
                        )
                        self.db.add(progress)

                    await self.db.flush()
                    return selected[:count]

            # Fallback: Use adaptive recommendation service for intelligent matching
            adaptive_service = AdaptiveRecommendationService(self.db)
            recommendation = await adaptive_service.get_recommendations(
                user=user,
                limit=count,
                min_difficulty=max(1, difficulty_level - 1),
                max_difficulty=min(8, difficulty_level + 1),
                
                learning_path="challenge",
            )

            # Extract exercise IDs from recommendations
            recommended_ids = [
                rec["exercise_id"] for rec in recommendation.get("recommendations", [])
            ]

            if recommended_ids:
                # Fetch recommended exercises
                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                # Preserve recommendation order
                selected = [
                    exercises_map[eid]
                    for eid in recommended_ids
                    if eid in exercises_map
                ]

                if len(selected) >= count:
                    # Create progress records
                    for i, ex in enumerate(selected[:count]):
                        progress = ArenaExerciseProgress(
                            user_id=user_id,
                            
                            exercise_id=ex.id,
                            exercise_index=i,
                            is_unlocked=(i == 0),
                        )
                        self.db.add(progress)

                    await self.db.flush()
                    return selected[:count]

        # Fallback: traditional random selection if adaptive fails
        # Challenge path is independent of courses - select from all verified exercises
        logger.info(f"Challenge path: selecting {count} exercises from all verified exercises (difficulty_level={difficulty_level})")

        # Try to get exercises with matching difficulty first
        exercises_result = await self.db.execute(
            select(Exercise)
            .where(
                Exercise.is_verified,
                Exercise.difficulty == difficulty_level,
            )
            .limit(count * 3)
        )
        all_exercises = exercises_result.scalars().all()

        # If not enough, get exercises within difficulty range
        if len(all_exercises) < count:
            exercises_result = await self.db.execute(
                select(Exercise)
                .where(
                    Exercise.is_verified,
                    Exercise.difficulty >= max(1, difficulty_level - 1),
                    Exercise.difficulty <= min(8, difficulty_level + 1),
                )
                .limit(count * 3)
            )
            all_exercises = exercises_result.scalars().all()

        # If still not enough, gradually lower min difficulty but never exceed max
        # This ensures new users always get easy problems, never hard ones
        if len(all_exercises) < count:
            exercises_result = await self.db.execute(
                select(Exercise)
                .where(
                    Exercise.is_verified,
                    Exercise.difficulty >= 1,
                    Exercise.difficulty <= min(8, difficulty_level + 1),
                )
                .limit(count * 3)
            )
            all_exercises = exercises_result.scalars().all()

        if len(all_exercises) < count:
            raise ValueError(f"Not enough verified exercises available (found {len(all_exercises)}, need {count})")

        selected = random.sample(list(all_exercises), count)

        for i, ex in enumerate(selected):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                
                exercise_id=ex.id,
                exercise_index=i,
                is_unlocked=(i == 0),
            )
            self.db.add(progress)

        await self.db.flush()
        return selected

    # ========================================
    # Progress Methods
    # ========================================

    async def get_progress(
        self,
        user_id: str,
        
    ) -> dict:
        """Get current progress for challenge path"""
        progress_records = await self._get_user_progress(user_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "exercises": [],
                "correct_count": 0,
                "completed_count": 0,
                "total_stars_earned": 0,
                "current_index": 0,
            }

        # Get exercises
        exercise_ids = [p.exercise_id for p in progress_records]
        exercises_result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {ex.id: ex for ex in exercises_result.scalars().all()}

        # Find current index (first incomplete or first after last completed)
        current_index = 0
        for i, p in enumerate(progress_records):
            if not p.is_completed:
                current_index = i
                break
            current_index = i + 1
        if current_index >= len(progress_records):
            current_index = len(progress_records) - 1

        # Build progress list with full exercise content
        progress_list = []
        for p in progress_records:
            ex = exercises.get(p.exercise_id)
            if ex:
                progress_list.append(
                    {
                        "exercise_id": p.exercise_id,
                        "exercise_index": p.exercise_index,
                        "is_completed": p.is_completed,
                        "is_correct": p.is_correct,
                        "is_unlocked": p.is_unlocked,
                        "saved_code": (p.saved_codes or {}).get(p.current_language, ""),
                        "current_language": p.current_language,
                        "title": (ex.content or {}).get(
                            "title", f"题目 {p.exercise_index + 1}"
                        ),
                        "difficulty": ex.difficulty,
                        # 完整题目内容
                        "content": {
                            "text": (ex.content or {}).get("text", ""),
                            "title": (ex.content or {}).get("title", ""),
                            "description": (ex.content or {}).get("description", ""),
                            "options": (ex.content or {}).get("options", []),
                            "code_template": (ex.content or {}).get(
                                "code_template", ""
                            ),
                            "input_format": (ex.content or {}).get("input_format", ""),
                            "output_format": (ex.content or {}).get(
                                "output_format", ""
                            ),
                            "sample_input": (ex.content or {}).get("sample_input", ""),
                            "sample_output": (ex.content or {}).get(
                                "sample_output", ""
                            ),
                            "samples": (ex.content or {}).get("samples", []),
                            "time_limit": (ex.content or {}).get("time_limit", 1000),
                            "memory_limit": (ex.content or {}).get("memory_limit", 256),
                        },
                        "knowledge_points": ex.knowledge_points or [],
                        "test_cases": ex.test_cases
                        if ex.type == "programming"
                        else None,
                        "type": ex.type,
                        "z_id": ex.z_id,
                    }
                )

        # Calculate stats
        correct_count = sum(1 for p in progress_records if p.is_correct)
        completed_count = sum(1 for p in progress_records if p.is_completed)
        # Sum up all stars earned (positive=earned, negative=lost)
        total_stars_earned = sum(p.stars_awarded for p in progress_records)

        return {
            "total_exercises": len(progress_records),
            "exercises": progress_list,
            "correct_count": correct_count,
            "completed_count": completed_count,
            "total_stars_earned": total_stars_earned,
            "current_index": current_index,
        }

    async def get_exercise_by_id(
        self,
        user_id: str,
        
        exercise_id: int,
    ) -> Optional[dict]:
        """Get specific exercise progress by exercise_id (for wrong book / favorites)"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return None

        # Get exercise
        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()
        if not exercise:
            return None

        return {
            "exercise_id": progress.exercise_id,
            "exercise_index": progress.exercise_index,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "is_unlocked": progress.is_unlocked,
            "saved_code": (progress.saved_codes or {}).get(
                progress.current_language, ""
            ),
            "current_language": progress.current_language,
            "title": (exercise.content or {}).get(
                "title", f"题目 {progress.exercise_index + 1}"
            ),
            "difficulty": exercise.difficulty,
            "exercise": exercise,
        }

    async def get_exercise_by_index(
        self,
        user_id: str,
        
        exercise_index: int,
    ) -> Optional[dict]:
        """Get exercise by its index in the challenge path"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                
                ArenaExerciseProgress.exercise_index == exercise_index,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return None

        return await self.get_exercise_by_id(user_id, progress.exercise_id)

    # ========================================
    # Action Methods
    # ========================================

    async def submit_exercise(
        self,
        user_id: str,

        exercise_id: int,
        code: str,
        language: str,
        test_results: list[dict],
        time_spent: Optional[int] = None,
        hint_used: bool = False,
    ) -> dict:
        """Submit exercise answer and update progress

        Args:
            user_id: User ID

            exercise_id: Exercise ID
            code: Submitted code
            language: Programming language
            test_results: Test results from Judge0
            time_spent: Time spent on exercise in seconds (for hybrid recommendation)
            hint_used: Whether user used hints (for hybrid recommendation)
        """
        # Get progress record
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,

                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress record not found")

        # Check if user is a test account and exercise_index < 3
        # Test accounts can pass first 3 exercises without verification
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        is_test_account = user.is_test_account if user else False
        is_first_three = progress.exercise_index < 3

        # Determine if correct using strict parsing to avoid truthiness bugs.
        # For test accounts on first 3 exercises, always pass
        if is_test_account and is_first_three:
            all_passed = True
            logger.info(f"[TEST_ACCOUNT] User {user_id[:8]}... is test account, exercise_index={progress.exercise_index}, auto-passing")
        else:
            all_passed = self._all_test_cases_passed(test_results)
        now = datetime.utcnow()

        # Update progress
        progress.is_completed = True
        progress.is_correct = all_passed
        progress.last_attempt_at = now
        progress.attempt_count += 1
        progress.current_language = language

        # Save code for this language
        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes

        if not progress.first_attempt_at:
            progress.first_attempt_at = now

        if all_passed and not progress.correct_at:
            progress.correct_at = now

        # Record behavior data for hybrid recommendation
        if time_spent is not None:
            progress.time_spent = time_spent
        if hint_used:
            progress.hint_used = True
        # Record first attempt correctness
        if progress.attempt_count == 1:
            progress.first_attempt_correct = all_passed

        exercise_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = exercise_result.scalar_one_or_none()

        # Collect wrong question if incorrect
        added_to_wrong_book = False
        if not all_passed and exercise:
            # Use exercise_key format: arena-{courseId}-{exerciseId}
            exercise_key = f"arena-global-{exercise_id}"
            await wrong_question_service.collect_wrong_question_by_key(
                db=self.db,
                user_id=user_id,
                exercise_key=exercise_key,
                user_answer=code,
                exercise_id=exercise_id,
                exercise_content=exercise.content,
                exercise_type=exercise.type,
                knowledge_points=exercise.knowledge_points,
            )
            added_to_wrong_book = True

        if exercise:
            exercise_title = (
                (exercise.content or {}).get("title")
                or (exercise.content or {}).get("text")
                or f"挑战题目 {progress.exercise_index + 1}"
            )
            activity = ActivityLog(
                user_id=user_id,
                activity_type="exercise_complete",
                chapter_id=exercise.chapter_id,
                description=f"挑战之路完成练习：{exercise_title}",
                extra_data={
                    "learning_path": "challenge",
                    "learning_path_label": "挑战之路",
                    
                    "exercise_id": exercise_id,
                    "exercise_index": progress.exercise_index,
                    "exercise_title": exercise_title,
                    "is_correct": all_passed,
                    "difficulty": exercise.difficulty,
                },
            )
            self.db.add(activity)

        # Unlock next exercise (find next exercise with higher index, not necessarily +1)
        next_unlocked = False
        next_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                
                ArenaExerciseProgress.exercise_index > progress.exercise_index,
            ).order_by(ArenaExerciseProgress.exercise_index).limit(1)
        )
        next_progress = next_result.scalar_one_or_none()
        if next_progress and not next_progress.is_unlocked:
            next_progress.is_unlocked = True
            next_unlocked = True

        # Update tier and stars (段位和星星更新)
        # 新逻辑：每次提交都会计算星星变化
        stars_earned = 0
        tier_changed = False
        new_tier = None
        new_sub_tier = None
        new_stars = 0
        promoted = False
        demoted = False

        # Get or create user arena profile
        profile_result = await self.db.execute(
            select(UserArenaProfile).where(
                UserArenaProfile.user_id == user_id,
            )
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            profile = UserArenaProfile(
                user_id=user_id,
                
            )
            self.db.add(profile)
            await self.db.flush()
            logger.info(f"[STARS] Created new profile for user {user_id[:8]}... ")

        # Get current tier info (always needed for response)
        current_tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
        current_sub_tier = profile.sub_tier if profile.sub_tier else 4
        current_stars = profile.stars if profile.stars else 0

        # Initialize result for tier operations
        tier_result = None

        # Get stars_deducted for this exercise (use getattr for backward compatibility)
        stars_deducted = getattr(progress, 'stars_deducted', None)
        if stars_deducted is None:
            # Fallback: calculate from stars_awarded if stars_deducted doesn't exist
            # stars_awarded negative means deducted, but we need separate tracking
            stars_deducted = abs(min(0, progress.stars_awarded)) if progress.stars_awarded < 0 else 0

        logger.info("[STARS] === Submit Exercise ===")
        logger.info(f"[STARS] User: {user_id[:8]}...,  Exercise: {exercise_id}")
        logger.info(f"[STARS] is_correct: {all_passed}, attempt_count: {progress.attempt_count}, difficulty: {exercise.difficulty if exercise else '?'}")
        logger.info(f"[STARS] stars_awarded: {progress.stars_awarded}, stars_deducted: {stars_deducted}")
        logger.info(f"[STARS] Current profile - tier: {current_tier.value}, sub_tier: {current_sub_tier}, stars: {current_stars}")

        # 检查是否已经做对过（已经获得正的星星奖励）
        already_correct = progress.stars_awarded > 0

        if already_correct:
            # 已经做对过了，不再处理星星
            new_tier = current_tier
            new_sub_tier = current_sub_tier
            new_stars = current_stars
            logger.info(f"[STARS] Already correct before (stars_awarded={progress.stars_awarded}), no change")
        else:
            # 还没做对过，计算星星
            if all_passed:
                # 做对了！只给基础奖励
                base_reward = tier_service.get_base_reward(exercise.difficulty) if exercise else 1
                stars_earned = base_reward
                logger.info(f"[STARS] CORRECT! base_reward={base_reward}, total=+{stars_earned}")
            else:
                # 做错了，检查是否扣星
                stars_earned = tier_service.calculate_stars_earned(
                    accuracy=0.0,
                    difficulty=exercise.difficulty if exercise else 1,
                    attempt_count=progress.attempt_count,
                    total_deducted=stars_deducted,
                )
                logger.info(f"[STARS] WRONG. attempt_count={progress.attempt_count}, stars_deducted={stars_deducted}, result={stars_earned}")

            # 记录星星变化
            progress.stars_awarded = stars_earned

            # 如果扣星了，更新 stars_deducted
            if stars_earned < 0 and hasattr(progress, 'stars_deducted'):
                progress.stars_deducted = stars_deducted + abs(stars_earned)
                logger.info(f"[STARS] Updated stars_deducted to {progress.stars_deducted}")

            if stars_earned > 0:
                # Add stars
                tier_result = tier_service.add_stars(
                    tier=current_tier,
                    sub_tier=current_sub_tier,
                    current_stars=current_stars,
                    stars_earned=stars_earned,
                )
                new_tier = tier_result.tier
                new_sub_tier = tier_result.sub_tier
                new_stars = tier_result.stars
                promoted = tier_result.promoted
                logger.info(f"[STARS] Add stars result - new_tier: {new_tier.value}, new_sub_tier: {new_sub_tier}, new_stars: {new_stars}, promoted: {promoted}")
            elif stars_earned < 0:
                # Remove stars
                tier_result = tier_service.remove_stars(
                    tier=current_tier,
                    sub_tier=current_sub_tier,
                    current_stars=current_stars,
                    stars_lost=abs(stars_earned),
                    protection_remaining=profile.protection_remaining or 0,
                )
                new_tier = tier_result.tier
                new_sub_tier = tier_result.sub_tier
                new_stars = tier_result.stars
                demoted = tier_result.demoted
                logger.info(f"[STARS] Remove stars result - new_tier: {new_tier.value}, new_sub_tier: {new_sub_tier}, new_stars: {new_stars}, demoted: {demoted}")

                # Update protection remaining
                profile.protection_remaining = tier_result.protection_remaining
            else:
                # No change
                new_tier = current_tier
                new_sub_tier = current_sub_tier
                new_stars = current_stars
                logger.info("[STARS] No stars change (stars_earned == 0)")

            # Update profile
            profile.tier = new_tier.value
            profile.sub_tier = new_sub_tier
            profile.stars = new_stars
            logger.info(f"[STARS] Updated profile - tier: {profile.tier}, sub_tier: {profile.sub_tier}, stars: {profile.stars}")

            # Update highest tier if promoted
            if promoted:
                highest_tier, highest_sub = tier_service.update_highest_tier(
                    profile.highest_tier,
                    profile.highest_sub_tier,
                    new_tier,
                    new_sub_tier,
                )
                profile.highest_tier = highest_tier.value if isinstance(highest_tier, TierRank) else highest_tier
                profile.highest_sub_tier = highest_sub

            tier_changed = (new_tier != current_tier or new_sub_tier != current_sub_tier)
            new_tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
            new_sub_tier = profile.sub_tier if profile.sub_tier else 4
            new_stars = profile.stars if profile.stars else 0

        # Update UserArenaProfile statistics (for quick lookup) - BEFORE commit
        try:
            await self._update_arena_profile_stats(profile, user_id)
        except Exception as e:
            logger.warning(f"Failed to update arena profile stats: {e}")

        # Award cores for correct answer in challenge path
        cores_earned = 0
        if all_passed and stars_earned > 0:  # Only award cores on first correct
            try:
                core_service = CoreService(self.db)
                cores_earned = CORE_REWARD_CHALLENGE_CORRECT
                await core_service.earn_cores(
                    user_id=user_id,
                    amount=cores_earned,
                    category="arena",
                    reference_type="exercise",
                    reference_id=str(exercise_id),
                    description="挑战之路答对题目",
                )
                logger.info(f"[CORE] Awarded {cores_earned} cores to user {user_id[:8]}... for correct challenge exercise")
            except Exception as e:
                logger.warning(f"Failed to award cores: {e}")
                cores_earned = 0

        # Record tier transaction if stars changed
        if stars_earned != 0 or promoted or demoted:
            try:
                from app.services.tier_transaction_service import TierTransactionService
                tier_tx_service = TierTransactionService(self.db)
                used_protection = getattr(tier_result, 'used_protection', False) if tier_result and stars_earned < 0 else False
                await tier_tx_service.record_transaction(
                    user_id=user_id,
                    course_id=None,  # Arena is global, no course_id
                    tier_before=current_tier.value if current_tier else TierRank.BRONZE.value,
                    sub_tier_before=current_sub_tier,
                    stars_before=current_stars,
                    tier_after=new_tier.value if new_tier else TierRank.BRONZE.value,
                    sub_tier_after=new_sub_tier,
                    stars_after=new_stars,
                    stars_change=stars_earned,
                    promoted=promoted,
                    demoted=demoted,
                    used_protection=used_protection,
                    protection_remaining=profile.protection_remaining or 0,
                    source="arena_challenge",
                    reference_id=str(exercise_id),
                    description=f"挑战之路答题 - {'答对' if all_passed else '答错'}",
                )
                logger.info(f"[TierTx] Recorded tier transaction for user {user_id[:8]}... stars_change={stars_earned}")
            except Exception as e:
                logger.warning(f"Failed to record tier transaction: {e}")

        await self.db.commit()
        logger.info(f"[STARS] After commit - profile.stars: {profile.stars}")

        # Update user profile embedding for hybrid recommendation (async, non-blocking)
        try:
            profile_service = UserProfileService(self.db)
            await profile_service.update_after_exercise(
                user_id=user_id,
                exercise_id=exercise_id,
                is_correct=all_passed,
                course_id=None,  # Arena is global, no course_id
                time_spent=time_spent,
                hint_used=hint_used,
                first_attempt_correct=(progress.attempt_count == 1 and all_passed),
            )
        except Exception as e:
            # Log but don't fail the submission
            logger.warning(f"Failed to update user profile: {e}")

        logger.info("[STARS] === Returning result ===")
        logger.info(f"[STARS] stars_earned: {stars_earned}, tier_changed: {tier_changed}")
        logger.info(f"[STARS] new_tier: {new_tier.value if new_tier else None}, new_sub_tier: {new_sub_tier}, new_stars: {new_stars}")

        # 判断是否是第一次做对/做错
        first_time_correct = all_passed and progress.attempt_count == 1
        first_time_wrong = not all_passed and progress.attempt_count == 1

        return {
            "is_correct": all_passed,
            "test_results": test_results,
            "stars_earned": stars_earned,
            "cores_earned": cores_earned,
            "next_unlocked": next_unlocked,
            "added_to_wrong_book": added_to_wrong_book,
            "tier_changed": tier_changed,
            "new_tier": new_tier.value if new_tier else None,
            "new_sub_tier": new_sub_tier,
            "new_stars": new_stars,
            "promoted": promoted,
            "demoted": demoted,
            "first_time_correct": first_time_correct,
            "first_time_wrong": first_time_wrong,
        }

    async def save_code(
        self,
        user_id: str,
        
        exercise_id: int,
        code: str,
        language: str,
    ) -> bool:
        """Save code for a specific language"""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return False

        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes
        progress.current_language = language

        await self.db.commit()
        return True

    async def switch_exercise(
        self,
        user_id: str,
        
        target_index: int,
    ) -> dict:
        """Switch to a different exercise by index"""
        # Get total count
        count_result = await self.db.execute(
            select(func.count())
            .select_from(ArenaExerciseProgress)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                
            )
        )
        total = count_result.scalar() or 0

        if target_index < 0 or target_index >= total:
            raise ValueError("Invalid exercise index")

        # Get target progress
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                
                ArenaExerciseProgress.exercise_index == target_index,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress not found")

        # Check if unlocked
        if not progress.is_unlocked:
            raise ValueError("Exercise is locked")

        # Get exercise
        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == progress.exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()

        return {
            "exercise_id": progress.exercise_id,
            "saved_code": (progress.saved_codes or {}).get(
                progress.current_language, ""
            ),
            "current_language": progress.current_language,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "exercise": exercise,
        }

    async def append_exercises(
        self,
        user_id: str,

        difficulty_level: Optional[int] = None,
        count: int = 5,
    ) -> list[int]:
        """Append more exercises to the challenge path using adaptive recommendation"""
        # Get current max index
        max_index_result = await self.db.execute(
            select(func.max(ArenaExerciseProgress.exercise_index)).where(
                ArenaExerciseProgress.user_id == user_id,

            )
        )
        max_index = max_index_result.scalar() or -1

        # Get existing exercise IDs to exclude
        existing_result = await self.db.execute(
            select(ArenaExerciseProgress.exercise_id).where(
                ArenaExerciseProgress.user_id == user_id,

            )
        )
        existing_ids = list(set(row[0] for row in existing_result.fetchall()))

        # Infer difficulty from existing exercises if not provided
        if difficulty_level is None:
            # Get existing exercises to calculate average difficulty
            existing_exercises_result = await self.db.execute(
                select(Exercise)
                .where(Exercise.id.in_(existing_ids))
                .limit(100)
            )
            existing_exercises = list(existing_exercises_result.scalars().all())
            if existing_exercises:
                avg_difficulty = sum(ex.difficulty for ex in existing_exercises) / len(existing_exercises)
                difficulty_level = max(1, min(8, round(avg_difficulty)))
            else:
                difficulty_level = 1  # Default to easiest for new users

        # Get user for adaptive recommendation
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        selected = []

        if user:
            # Use adaptive recommendation service for intelligent matching
            adaptive_service = AdaptiveRecommendationService(self.db)
            recommendation = await adaptive_service.get_recommendations(
                user=user,
                limit=count,
                min_difficulty=max(1, difficulty_level - 1),
                max_difficulty=min(8, difficulty_level + 1),

                learning_path="challenge",
                exclude_ids=existing_ids,
            )

            recommended_ids = [
                rec["exercise_id"] for rec in recommendation.get("recommendations", [])
            ]

            if recommended_ids:
                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                selected = [
                    exercises_map[eid]
                    for eid in recommended_ids
                    if eid in exercises_map
                ]

        # Fallback: traditional random selection if adaptive fails
        if len(selected) < count:
            all_exclude = existing_ids + [ex.id for ex in selected]

            exercises_result = await self.db.execute(
                select(Exercise)
                .where(
                    Exercise.is_verified,
                    Exercise.difficulty == difficulty_level,
                    ~Exercise.id.in_(all_exclude),
                )
                .limit(count * 2)
            )
            all_exercises = exercises_result.scalars().all()

            # 如果还不够，放宽到难度范围 ±2，但保持上限不超过 difficulty_level + 2
            if len(all_exercises) < count - len(selected):
                exercises_result = await self.db.execute(
                    select(Exercise)
                    .where(
                        Exercise.is_verified,
                        Exercise.difficulty >= max(1, difficulty_level - 2),
                        Exercise.difficulty <= min(8, difficulty_level + 2),
                        ~Exercise.id.in_(all_exclude),
                    )
                    .limit(count * 2)
                )
                all_exercises = exercises_result.scalars().all()

            # 最后兜底：只限制最大难度，确保不超出用户选择的难度太多
            if len(all_exercises) < count - len(selected):
                exercises_result = await self.db.execute(
                    select(Exercise)
                    .where(
                        Exercise.is_verified,
                        Exercise.difficulty >= 1,
                        Exercise.difficulty <= min(8, difficulty_level + 2),
                        ~Exercise.id.in_(all_exclude),
                    )
                    .limit(count * 2)
                )
                all_exercises = exercises_result.scalars().all()

            remaining = (
                random.sample(
                    list(all_exercises), min(count - len(selected), len(all_exercises))
                )
                if all_exercises
                else []
            )
            selected.extend(remaining)

        if not selected:
            return []

        # Check if last exercise is completed (for unlocking first new one)
        last_exercise_completed = False
        if max_index >= 0:
            last_result = await self.db.execute(
                select(ArenaExerciseProgress).where(
                    ArenaExerciseProgress.user_id == user_id,
                    
                    ArenaExerciseProgress.exercise_index == max_index,
                )
            )
            last_progress = last_result.scalar_one_or_none()
            last_exercise_completed = (
                last_progress.is_completed if last_progress else False
            )

        new_ids = []
        for i, ex in enumerate(selected):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                
                exercise_id=ex.id,
                exercise_index=max_index + 1 + i,
                is_unlocked=(i == 0 and (max_index < 0 or last_exercise_completed)),
            )
            self.db.add(progress)
            new_ids.append(ex.id)

        await self.db.commit()
        return new_ids

    async def _update_arena_profile_stats(
        self,
        profile: UserArenaProfile,
        user_id: str,
    ) -> None:
        """Update UserArenaProfile statistics from ArenaExerciseProgress records."""
        # Get all progress records joined with exercises for difficulty info
        result = await self.db.execute(
            select(ArenaExerciseProgress, Exercise)
            .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
            .where(ArenaExerciseProgress.user_id == user_id)
            .order_by(ArenaExerciseProgress.exercise_index)
        )
        rows = list(result.all())
        if not rows:
            return

        progresses = [p for p, _ in rows]
        exercises_map = {p.exercise_id: ex for p, ex in rows}

        total = len(progresses)
        completed = [p for p in progresses if p.is_completed]
        correct = [p for p in progresses if p.is_correct]
        total_attempts = sum(p.attempt_count for p in progresses)
        times_spent = [p.time_spent for p in progresses if p.time_spent]

        # Streak calculation (ordered by exercise_index)
        best_streak = 0
        current_run = 0
        for p in progresses:
            if p.is_correct:
                current_run += 1
                best_streak = max(best_streak, current_run)
            else:
                current_run = 0

        # Current streak = trailing consecutive correct answers
        current_streak = 0
        for p in reversed(progresses):
            if p.is_correct:
                current_streak += 1
            else:
                break

        # Highest difficulty among completed exercises
        highest_difficulty = 0
        for p in completed:
            ex = exercises_map.get(p.exercise_id)
            if ex and ex.difficulty > highest_difficulty:
                highest_difficulty = ex.difficulty

        # Update profile
        profile.total_challenges = len(completed)
        profile.wins = len(correct)
        profile.losses = len(completed) - len(correct)
        profile.best_streak = best_streak
        profile.current_streak = current_streak
        profile.highest_difficulty = highest_difficulty
        profile.total_submissions = total_attempts
        profile.avg_accuracy = len(correct) / total if total > 0 else 0.0
        profile.avg_time_spent = sum(times_spent) / len(times_spent) if times_spent else 0.0

    async def get_stats(
        self,
        user_id: str,
        
    ) -> dict:
        """Get challenge path statistics"""
        progress_records = await self._get_user_progress(user_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "completed_count": 0,
                "correct_count": 0,
                "total_xp": 0,
            }

        completed = sum(1 for p in progress_records if p.is_completed)
        correct = sum(1 for p in progress_records if p.is_correct)

        return {
            "total_exercises": len(progress_records),
            "completed_count": completed,
            "correct_count": correct,
            "total_xp": correct * 10,
        }


def get_challenge_path_service(db: AsyncSession) -> ChallengePathService:
    """Get ChallengePathService instance"""
    return ChallengePathService(db)


# Backward compatibility alias
ArenaInfiniteService = ChallengePathService
get_arena_infinite_service = get_challenge_path_service
