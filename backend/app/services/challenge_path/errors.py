class ChallengePathError(Exception):
    """Base class for expected Arena lifecycle failures."""


class ChallengeSubmissionError(ChallengePathError):
    """Base class for expected Arena submission failures."""


class InsufficientChallengeExercisesError(ChallengePathError):
    def __init__(self, found: int, required: int) -> None:
        super().__init__(
            f"Not enough verified exercises available (found {found}, need {required})"
        )


class InvalidChallengeExerciseIndexError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Invalid exercise index")


class ChallengeProgressIndexNotFoundError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Progress not found")


class ChallengeExerciseLockedError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Exercise is locked")


class ChallengeExerciseDetailNotFoundError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Exercise not found in challenge path")


class ChallengeExerciseNotFoundError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(f"Exercise {exercise_id} not found")


class ChallengeProgressNotFoundError(ChallengePathError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(f"Progress record for exercise {exercise_id} not found")


class UnsupportedChallengeLanguageError(ChallengeSubmissionError):
    def __init__(self, language: str) -> None:
        super().__init__(f"Unsupported language for judging: {language}")


class MissingChallengeTestCasesError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(
            f"Programming exercise {exercise_id} has no backend test cases"
        )


class JudgeUnavailableError(ChallengeSubmissionError):
    def __init__(self, message: str = "Judge service unavailable") -> None:
        super().__init__(message)
