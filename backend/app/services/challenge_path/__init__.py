"""Focused services for the challenge path."""

from .errors import (
    ChallengeExerciseDetailNotFoundError,
    ChallengeExerciseLockedError,
    ChallengeExerciseNotFoundError,
    ChallengePathError,
    ChallengeProgressIndexNotFoundError,
    ChallengeProgressNotFoundError,
    ChallengeSubmissionError,
    InsufficientChallengeExercisesError,
    InvalidChallengeExerciseIndexError,
    JudgeUnavailableError,
    MissingChallengeTestCasesError,
    UnsupportedChallengeLanguageError,
)
from .progress import ChallengeProgressService
from .responses import map_exercise_detail_response, map_exercise_summary, map_switch_response
from .rewards import ChallengeRewardService
from .selection import ChallengeSelectionService
from .submission import ChallengeSubmissionService
from .submission_state import (
    ChallengeSubmissionState,
    ChallengeSubmissionStateService,
)

__all__ = [
    "ChallengeExerciseDetailNotFoundError",
    "ChallengeExerciseLockedError",
    "ChallengeExerciseNotFoundError",
    "ChallengePathError",
    "ChallengeProgressIndexNotFoundError",
    "ChallengeProgressService",
    "ChallengeProgressNotFoundError",
    "ChallengeRewardService",
    "ChallengeSelectionService",
    "ChallengeSubmissionError",
    "ChallengeSubmissionService",
    "ChallengeSubmissionState",
    "ChallengeSubmissionStateService",
    "InsufficientChallengeExercisesError",
    "InvalidChallengeExerciseIndexError",
    "JudgeUnavailableError",
    "MissingChallengeTestCasesError",
    "UnsupportedChallengeLanguageError",
    "map_exercise_summary",
    "map_switch_response",
    "map_exercise_detail_response",
]
